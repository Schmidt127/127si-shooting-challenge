"""Byte-exact Production formula rollback texts for Stage Z closeout."""

from __future__ import annotations

from .clock_override import PRODUCTION_ACTIVITY_DATE_IS_FUTURE_FORMULA

PRODUCTION_SUBMITTED_SAME_DAY_FORMULA = """IF(
  AND(
    {Submitted At},
    {Activity Date}
  ),
  IF(
    DATETIME_FORMAT(
      SET_TIMEZONE({Submitted At}, "America/Denver"),
      "YYYY-MM-DD"
    )
    =
    DATETIME_FORMAT(
      SET_TIMEZONE({Activity Date}, "UTC"),
      "YYYY-MM-DD"
    ),
    1,
    0
  ),
  0
)"""

PRODUCTION_PERFECT_WEEK_GRACE_ELIGIBLE_FORMULA = """IF(
  OR(
    {Perfect Week Manual Exception?},
    AND(
      {Count This Submission?} = 1,
      {Activity Date},
      {Submitted At},
      DATETIME_FORMAT(
        SET_TIMEZONE({Activity Date}, "America/Denver"),
        "YYYY-MM-DD"
      ) <= DATETIME_FORMAT(TODAY(), "YYYY-MM-DD"),
      DATETIME_DIFF(
        {Submitted At},
        DATETIME_PARSE(
          DATETIME_FORMAT(
            DATEADD(
              DATETIME_PARSE(
                DATETIME_FORMAT(
                  SET_TIMEZONE({Activity Date}, "America/Denver"),
                  "YYYY-MM-DD"
                ),
                "YYYY-MM-DD"
              ),
              1,
              "days"
            ),
            "YYYY-MM-DD"
          ) & " 00:00",
          "YYYY-MM-DD HH\\\\:mm"
        ),
        "hours"
      ) <= 48
    )
  ),
  1,
  0
)"""

PRODUCTION_FORMULA_ROLLBACK: tuple[tuple[str, str, str], ...] = (
    ("Submissions", "Activity Date Is Future?", PRODUCTION_ACTIVITY_DATE_IS_FUTURE_FORMULA),
    ("Submissions", "Submitted Same Day?", PRODUCTION_SUBMITTED_SAME_DAY_FORMULA),
    ("Submissions", "Perfect Week Grace Eligible?", PRODUCTION_PERFECT_WEEK_GRACE_ELIGIBLE_FORMULA),
)

FIELD_IDS = {
    "Activity Date Is Future?": "fldyFAjhbfaC4LlPb",
    "Submitted Same Day?": "fldE7G8H1O7HPYuIi",
    "Perfect Week Grace Eligible?": "fldLo2GO5aac6tPX1",
}
