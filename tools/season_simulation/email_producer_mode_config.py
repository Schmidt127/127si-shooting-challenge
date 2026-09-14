"""Non-writing email producer mode configuration validator.

Airtable automation ``input.config()`` values are UI-only and cannot be read
via the Airtable API. This module reports the **script-enforced defaults and
required UI values** for normal (live) Perfect season-sim email delivery.

Root cause note (T161924Z welcome):
  Automation **078A** sets Email Handoff Queue ``Test Mode?`` from
  ``input.config().testMode``, with ``cfg.testMode === undefined ? true : Boolean(cfg.testMode)``.
  Automation **079** copies that checkbox into the Hub ingress payload as
  ``testMode``. Hub then materializes ``Msg Send Mode = Test`` when true.

  Therefore a welcome handoff with ``Test Mode? = true`` / Hub ``Send Mode = Test``
  means 078A's UI input was absent, unset, or not boolean ``false`` at run time —
  not a Hub policy override and not a different producer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProducerModeExpectation:
    automation_code: str
    automation_name: str
    input_variable: str
    script_default_when_absent: str
    required_for_live_normal: str
    ui_field_location: str
    notes: str
    hub_effect: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EmailProducerModeReport:
    ok_for_documentation: bool
    api_readable: bool
    producers: list[ProducerModeExpectation] = field(default_factory=list)
    welcome_root_cause: str = ""
    mike_verify_checklist: list[str] = field(default_factory=list)
    stop_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok_for_documentation": self.ok_for_documentation,
            "api_readable": self.api_readable,
            "producers": [p.to_dict() for p in self.producers],
            "welcome_root_cause": self.welcome_root_cause,
            "mike_verify_checklist": list(self.mike_verify_checklist),
            "stop_reasons": list(self.stop_reasons),
        }


# Canonical expectations for normal Perfect email-enabled simulation.
LIVE_NORMAL_PRODUCERS: tuple[ProducerModeExpectation, ...] = (
    ProducerModeExpectation(
        automation_code="078A",
        automation_name="078A - Enrollment -> Create WELCOME Email Handoff",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location=(
            "Airtable Automations → 078A → Script configuration → input variable "
            "`testMode` (must be present and set to boolean false; do not leave blank)"
        ),
        notes=(
            "Writes Email Handoff Queue.Test Mode? from input. "
            "JS uses Boolean(cfg.testMode); string 'false' would incorrectly become true."
        ),
        hub_effect="079 forwards Test Mode? → Hub testMode → Msg Send Mode Test|Live",
    ),
    ProducerModeExpectation(
        automation_code="071",
        automation_name="071 - Homework feedback email handoff",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location="Airtable Automations → 071 → input `testMode` = false",
        notes="Default true when input absent.",
        hub_effect="EHQ Test Mode? → 079 → Hub",
    ),
    ProducerModeExpectation(
        automation_code="073",
        automation_name="073 - Video feedback parent email handoff",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location="Airtable Automations → 073 → input `testMode` = false",
        notes="Default true when input absent.",
        hub_effect="EHQ Test Mode? → 079 → Hub",
    ),
    ProducerModeExpectation(
        automation_code="074",
        automation_name="074 - Weekly email Make/Hub handoff",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location="Airtable Automations → 074 → input `testMode` = false",
        notes="Default true when input absent.",
        hub_effect="EHQ Test Mode? → 079 → Hub",
    ),
    ProducerModeExpectation(
        automation_code="076",
        automation_name="076 - Daily submission Hub handoff",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location="Airtable Automations → 076 → input `testMode` = false",
        notes="Default true when input absent.",
        hub_effect="EHQ Test Mode? → 079 → Hub",
    ),
    ProducerModeExpectation(
        automation_code="117",
        automation_name="117 - Zoom recording approval email",
        input_variable="testMode",
        script_default_when_absent="true",
        required_for_live_normal="false (boolean)",
        ui_field_location="Airtable Automations → 117 → input `testMode` = false",
        notes="Default true when input absent.",
        hub_effect="EHQ Test Mode? → 079 → Hub",
    ),
    ProducerModeExpectation(
        automation_code="072",
        automation_name="072 - Build weekly email package",
        input_variable="sendModeInput",
        script_default_when_absent="(script-defined; verify live)",
        required_for_live_normal="live",
        ui_field_location="Airtable Automations → 072 → input `sendModeInput` = live",
        notes="Not a testMode checkbox; separate send-mode input.",
        hub_effect="Controls weekly package send plane",
    ),
    ProducerModeExpectation(
        automation_code="118",
        automation_name="118 - Weekly email batch",
        input_variable="dryRun / sendMode / includeSchmidt",
        script_default_when_absent="(script-defined; verify live)",
        required_for_live_normal="dryRun=false, sendMode=Live, includeSchmidt=false",
        ui_field_location=(
            "Airtable Automations → 118 → inputs dryRun=false, sendMode=Live, "
            "includeSchmidt=false"
        ),
        notes="UI-only; API cannot read.",
        hub_effect="Batch weekly Hub handoffs",
    ),
    ProducerModeExpectation(
        automation_code="119",
        automation_name="119 - Weekly email stage helper",
        input_variable="dryRun / includeSchmidt",
        script_default_when_absent="(script-defined; verify live)",
        required_for_live_normal="dryRun=false, includeSchmidt=false",
        ui_field_location=(
            "Airtable Automations → 119 → inputs dryRun=false, includeSchmidt=false"
        ),
        notes="UI-only; API cannot read.",
        hub_effect="Stage helper for weekly path",
    ),
    ProducerModeExpectation(
        automation_code="079",
        automation_name="079 - Send queue handoff to Communications Hub",
        input_variable="ingressSecret (only)",
        script_default_when_absent="n/a — required secret",
        required_for_live_normal="ingressSecret present; does not own testMode",
        ui_field_location=(
            "Airtable Automations → 079 → input `ingressSecret` present; "
            "leave unchanged. Test/Live comes from queue row Test Mode?."
        ),
        notes="Reads EHQ Test Mode? checkbox; forwards as Hub testMode.",
        hub_effect="Dispatcher only — mirrors producer Test Mode?",
    ),
)


def build_email_producer_mode_report() -> EmailProducerModeReport:
    """Return static expected modes (never calls Airtable; never sends mail)."""
    checklist = [
        f"{p.automation_code}: set {p.input_variable} → {p.required_for_live_normal}"
        for p in LIVE_NORMAL_PRODUCERS
        if p.automation_code != "079"
    ]
    checklist.append(
        "079: confirm ingressSecret present; do not change it; "
        "re-open 078A after save and confirm testMode persisted as boolean false"
    )
    return EmailProducerModeReport(
        ok_for_documentation=True,
        api_readable=False,
        producers=list(LIVE_NORMAL_PRODUCERS),
        welcome_root_cause=(
            "T161924Z WELCOME used Test Mode because 078A script defaults "
            "input.config().testMode to true when the UI input is absent/undefined "
            "(or non-boolean). 079 then forwarded Test Mode?=true to the Hub, which "
            "set Msg Send Mode=Test. Not a second athlete, not Hub allowlist policy, "
            "and not a silent harness override."
        ),
        mike_verify_checklist=checklist,
        stop_reasons=[],
    )


__all__ = [
    "EmailProducerModeReport",
    "LIVE_NORMAL_PRODUCERS",
    "ProducerModeExpectation",
    "build_email_producer_mode_report",
]
