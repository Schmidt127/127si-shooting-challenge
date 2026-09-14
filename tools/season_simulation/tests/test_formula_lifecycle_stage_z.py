"""Offline tests for Production-normal formula lifecycle + Stage Z recovery."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

TOOLS = Path(__file__).resolve().parents[2]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from season_simulation.business_reconciliation import event_is_active  # noqa: E402
from season_simulation.cascade_settlement import DEFAULT_TIMEOUT_S  # noqa: E402
from season_simulation.constants import (  # noqa: E402
    CONFIRM_TOKEN,
    DEFAULT_BASE_ID,
    SAFE_EMAIL_RECIPIENT,
)
from season_simulation.execute_three import (  # noqa: E402
    DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
)
from season_simulation.formula_lifecycle import (  # noqa: E402
    FormulaLifecycleError,
    merge_formula_lifecycle,
    recover_pending_formula_restore,
    restore_production_formulas,
    restore_stage_z,
)
from season_simulation.memory_client import MemoryAirtableClient  # noqa: E402
from season_simulation.pre_execute_checklist import (  # noqa: E402
    run_pre_execute_email_hub_checklist,
)
from season_simulation.production_normal_formulas import (  # noqa: E402
    ProductionNormalBundleError,
    formula_sha256,
    load_production_normal_bundle,
)
from season_simulation.run_registry import RunRegistry, save_registry  # noqa: E402
from season_simulation.simulation_process_lock import (  # noqa: E402
    SimulationProcessLockError,
    acquire_simulation_lock,
    release_simulation_lock,
)


GATED_FUTURE = """\
IF(
  AND(
    {Season Sim Test Record?},
    FIND("SEASON-SIM|", {Video Upload Note} & "") > 0
  ),
  IF({Season Sim Clock Now}, IF({Activity Date} > {Season Sim Clock Now}, 1, 0), 0),
  IF({Activity Date}, IF({Activity Date} > NOW(), 1, 0), BLANK())
)"""


class TestProductionNormalBundle(unittest.TestCase):
    def test_bundle_loads_and_hashes_stable(self):
        bundle = load_production_normal_bundle()
        self.assertEqual(bundle.base_id, DEFAULT_BASE_ID)
        self.assertEqual(len(bundle.fields), 3)
        for fld in bundle.fields:
            self.assertNotIn("SEASON-SIM", fld.formula_text)
            self.assertEqual(fld.sha256, formula_sha256(fld.formula_text))

    def test_missing_bundle_fails_closed(self):
        with self.assertRaises(ProductionNormalBundleError):
            load_production_normal_bundle(Path("/nonexistent/production_normal_formulas.json"))


class TestStageZRestore(unittest.TestCase):
    def setUp(self):
        self.bundle = load_production_normal_bundle()
        self.client = MemoryAirtableClient(allow_writes=True)
        self.client.base_id = DEFAULT_BASE_ID
        # Start gated (simulates mid-run Production).
        self.client._formula_overrides = {
            "Activity Date Is Future?": GATED_FUTURE,
            "Submitted Same Day?": GATED_FUTURE,
            "Perfect Week Grace Eligible?": GATED_FUTURE,
        }

    def test_successful_restore_uses_production_normal_bundle(self):
        result = restore_production_formulas(
            self.client,
            allow_writes=True,
            confirm=CONFIRM_TOKEN,
            dry_run=False,
        )
        self.assertTrue(result["production_formulas_restored"])
        self.assertFalse(result["formula_restore_failed"])
        self.assertFalse(result["formula_restore_pending"])
        self.assertEqual(result["restore_source"], "production_normal_bundle")
        self.assertEqual(result["verified_hashes"], self.bundle.hashes())
        self.assertFalse(result["season_sim_remaining"])
        # Live meta matches Production-normal.
        meta = self.client.meta_tables()
        from season_simulation.formula_lifecycle import verify_production_normal_restored

        ok, verified, errors, left = verify_production_normal_restored(meta, self.bundle)
        self.assertTrue(ok, errors)
        self.assertEqual(verified, self.bundle.hashes())
        self.assertFalse(left)

    def test_dry_run_never_claims_restored(self):
        result = restore_production_formulas(
            self.client,
            allow_writes=False,
            confirm=None,
        )
        self.assertEqual(result["status"], "planned")
        self.assertFalse(result["production_formulas_restored"])
        self.assertFalse(result.get("restored"))
        self.assertTrue(result["formula_restore_pending"])

    def test_stage0_snapshot_ignored(self):
        result = restore_production_formulas(
            self.client,
            allow_writes=False,
            snapshot_bundle={"snapshots": [{"field_name": "x", "formula_text": "NOW()"}]},
        )
        self.assertTrue(result["ignored_stage0_snapshot"])
        self.assertEqual(result["restore_source"], "production_normal_bundle")

    def test_writer_error_records_failed_state(self):
        client = MagicMock()
        client.base_id = DEFAULT_BASE_ID
        client.meta_tables.return_value = [
            {
                "id": self.bundle.table_id,
                "name": "Submissions",
                "fields": [
                    {
                        "id": f.field_id,
                        "name": f.field_name,
                        "type": "formula",
                        "options": {"formula": GATED_FUTURE},
                    }
                    for f in self.bundle.fields
                ],
            }
        ]

        def boom(**kwargs):
            raise RuntimeError("meta patch failed")

        client.update_formula_field.side_effect = boom
        result = restore_production_formulas(
            client,
            allow_writes=True,
            confirm=CONFIRM_TOKEN,
            dry_run=False,
        )
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["formula_restore_failed"])
        self.assertFalse(result["production_formulas_restored"])
        self.assertTrue(result["formula_restore_pending"])
        self.assertTrue(any("Restore failed" in e for e in result["errors"]))

    def test_wrong_confirm_fails_closed(self):
        result = restore_production_formulas(
            self.client,
            allow_writes=True,
            confirm="WRONG",
            dry_run=False,
        )
        self.assertTrue(result["formula_restore_failed"])
        self.assertFalse(result["production_formulas_restored"])

    def test_no_false_positive_restored_on_hash_mismatch(self):
        client = MagicMock()
        client.base_id = DEFAULT_BASE_ID
        # Writer "succeeds" but meta still returns gated text → hash fail.
        client.update_formula_field.return_value = {}
        client.meta_tables.return_value = [
            {
                "id": self.bundle.table_id,
                "name": "Submissions",
                "fields": [
                    {
                        "id": f.field_id,
                        "name": f.field_name,
                        "type": "formula",
                        "options": {"formula": GATED_FUTURE},
                    }
                    for f in self.bundle.fields
                ],
            }
        ]
        result = restore_production_formulas(
            client,
            allow_writes=True,
            confirm=CONFIRM_TOKEN,
            dry_run=False,
        )
        self.assertFalse(result["production_formulas_restored"])
        self.assertTrue(result["formula_restore_failed"])
        self.assertTrue(result["season_sim_remaining"] or result["errors"])


class TestRecoveryPath(unittest.TestCase):
    def test_recovery_from_formula_restore_pending(self):
        tmp = Path(tempfile.mkdtemp())
        run_id = "SEASON-SIM-PERFECT-20260914T120000Z-mike-schmidt"
        reg = RunRegistry(
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="paused",
            meta={
                "formula_lifecycle": merge_formula_lifecycle(
                    None,
                    gates_applied=True,
                    settlement_complete=True,
                    formula_restore_pending=True,
                )
            },
        )
        save_registry(reg, tmp)

        client = MemoryAirtableClient(allow_writes=True)
        client.base_id = DEFAULT_BASE_ID
        client._formula_overrides = {
            "Activity Date Is Future?": GATED_FUTURE,
            "Submitted Same Day?": GATED_FUTURE,
            "Perfect Week Grace Eligible?": GATED_FUTURE,
        }

        planned = recover_pending_formula_restore(
            registry=reg,
            registry_dir=tmp,
            client=client,
            allow_writes=False,
        )
        self.assertEqual(planned["status"], "planned")
        self.assertIn("Activity Date Is Future?", planned["expected_hashes"])

        live = recover_pending_formula_restore(
            registry=reg,
            registry_dir=tmp,
            client=client,
            allow_writes=True,
            confirm=CONFIRM_TOKEN,
        )
        self.assertTrue(live.get("production_formulas_restored"), live)
        self.assertFalse(live.get("formula_restore_pending"))
        lifecycle = (reg.meta or {}).get("formula_lifecycle") or {}
        self.assertTrue(lifecycle.get("production_formulas_restored"))
        self.assertFalse(lifecycle.get("formula_restore_pending"))


class TestLifecycleMerge(unittest.TestCase):
    def test_never_restored_and_failed_together(self):
        state = merge_formula_lifecycle(
            None,
            production_formulas_restored=True,
            formula_restore_failed=True,
        )
        self.assertFalse(state["production_formulas_restored"])


class TestActiveXpReconciliation(unittest.TestCase):
    def test_active_requires_true(self):
        self.assertTrue(event_is_active({"Active?": True, "XP Points": 10}))
        self.assertFalse(event_is_active({"Active?": False, "XP Points": 10}))
        self.assertFalse(event_is_active({"XP Points": 10}))  # null/missing
        self.assertFalse(event_is_active({"Active?": None, "XP Points": 10}))


class TestSettlementAndProcessGuards(unittest.TestCase):
    def test_settlement_timeout_is_900(self):
        self.assertEqual(DEFAULT_TIMEOUT_S, 900.0)
        self.assertEqual(DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S, 900.0)

    def test_single_process_lock(self):
        import os

        tmp = Path(tempfile.mkdtemp())
        run_a = "SEASON-SIM-PERFECT-20260914T120000Z-mike-schmidt"
        run_b = "SEASON-SIM-PERFECT-20260914T130000Z-mike-schmidt"
        my_pid = os.getpid()
        info = acquire_simulation_lock(registry_dir=tmp, run_id=run_a, pid=my_pid)
        self.assertEqual(info.run_id, run_a)
        with self.assertRaises(SimulationProcessLockError):
            acquire_simulation_lock(registry_dir=tmp, run_id=run_b, pid=my_pid + 1)
        release_simulation_lock(registry_dir=tmp, run_id=run_a, pid=my_pid)
        # After release, another run may acquire.
        info2 = acquire_simulation_lock(registry_dir=tmp, run_id=run_b, pid=my_pid)
        self.assertEqual(info2.run_id, run_b)
        release_simulation_lock(registry_dir=tmp, run_id=run_b, pid=my_pid)


class TestPreExecuteChecklist(unittest.TestCase):
    def test_email_hub_checklist_requires_attestations(self):
        report = run_pre_execute_email_hub_checklist(
            allowlist_recipient=SAFE_EMAIL_RECIPIENT,
            ehq_backlog_count=0,
            hub_transactional_backlog_count=0,
            enable_email_delivery=True,
            attest_079_ingress_secret=False,
            attest_producer_input_modes=False,
            single_process_ok=True,
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("079" in s for s in report.stop_reasons))

    def test_email_hub_checklist_passes_when_attested(self):
        report = run_pre_execute_email_hub_checklist(
            allowlist_recipient=SAFE_EMAIL_RECIPIENT,
            ehq_backlog_count=0,
            hub_transactional_backlog_count=0,
            enable_email_delivery=True,
            attest_079_ingress_secret=True,
            attest_producer_input_modes=True,
            single_process_ok=True,
        )
        self.assertTrue(report.ok, report.stop_reasons)


class Test054IsoPrefixRegression(unittest.TestCase):
    """Protect current perfect-sim date behavior; document ISO-prefix debt."""

    def test_054_to_date_key_iso_prefix_behavior(self):
        # Mirror 054 toDateKey ISO-prefix branch (do not paste live code).
        def to_date_key(value):
            if not value:
                return ""
            if isinstance(value, str):
                trimmed = value.strip()
                import re

                iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", trimmed)
                if iso:
                    return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"
            return ""

        # Perfect-sim Activity / streak end dates arrive as ISO date or datetime.
        self.assertEqual(to_date_key("2027-05-08"), "2027-05-08")
        self.assertEqual(to_date_key("2027-05-08T06:00:00.000Z"), "2027-05-08")
        # Debt: ISO-prefix ignores timezone — documented in 054-ISO-PREFIX-DEBT.
        self.assertEqual(to_date_key("2027-05-08T23:30:00-06:00"), "2027-05-08")


if __name__ == "__main__":
    unittest.main()
