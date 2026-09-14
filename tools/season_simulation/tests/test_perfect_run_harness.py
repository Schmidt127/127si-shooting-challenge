"""Perfect-run harness: Stage H, contract run_id, email mode docs, launch proof."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from season_simulation.cleanup import stage_h_post_cascade_hooks  # noqa: E402
from season_simulation.email_producer_mode_config import (  # noqa: E402
    build_email_producer_mode_report,
)
from season_simulation.execute_perfect import PERFECT_PROFILE  # noqa: E402
from season_simulation.live_write_contract import (  # noqa: E402
    build_contract_validation_for_client,
)
from season_simulation.perfect_launch_proof import run_perfect_launch_proof  # noqa: E402
from season_simulation.run_registry import new_perfect_run_id  # noqa: E402


class PerfectStageHTests(unittest.TestCase):
    def test_stage_h_accepts_perfect_run_id(self):
        rid = new_perfect_run_id()
        with tempfile.TemporaryDirectory() as tmp:
            report = stage_h_post_cascade_hooks(
                run_id=rid,
                registry_dir=Path(tmp),
                client=None,
                profile=PERFECT_PROFILE,
            )
        self.assertEqual(report["path"], "perfect_or_single")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["errors"], [])

    def test_stage_h_threeathlete_path_unchanged(self):
        rid = "SEASON-SIM-2027-20260914T120000Z-threeathlete"
        with tempfile.TemporaryDirectory() as tmp:
            report = stage_h_post_cascade_hooks(
                run_id=rid,
                registry_dir=Path(tmp),
                client=None,
                profile=None,
            )
        self.assertEqual(report["path"], "threeathlete")


class ContractRunIdTests(unittest.TestCase):
    def test_build_contract_validation_requires_run_id(self):
        import inspect

        sig = inspect.signature(build_contract_validation_for_client)
        self.assertIn("run_id", sig.parameters)
        param = sig.parameters["run_id"]
        self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY)


class EmailProducerModeTests(unittest.TestCase):
    def test_welcome_root_cause_documents_078a_default(self):
        report = build_email_producer_mode_report()
        self.assertFalse(report.api_readable)
        self.assertIn("078A", report.welcome_root_cause)
        self.assertIn("testMode", report.welcome_root_cause)
        producers = {p.automation_code: p for p in report.producers}
        self.assertEqual(producers["078A"].script_default_when_absent, "true")
        self.assertIn("false", producers["078A"].required_for_live_normal)


class PerfectLaunchProofTests(unittest.TestCase):
    def test_prove_perfect_launch_zero_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_perfect_launch_proof(
                out_dir=root / "out",
                registry_dir=root / "reg",
                client=None,
            )
        self.assertEqual(result["client_writes"], 0)
        self.assertTrue(result["ok"], result.get("errors") or result.get("checks"))
        names = {c["name"] for c in result["checks"]}
        for required in (
            "weekinfo_perfect_scenario",
            "stage_h_perfect_run_id",
            "exclusive_process_lock",
            "active_xp_oracle_4980",
            "settlement_timeout_900s",
            "recipient_hard_stop",
            "contract_validation_requires_run_id",
        ):
            self.assertIn(required, names)


if __name__ == "__main__":
    unittest.main()
