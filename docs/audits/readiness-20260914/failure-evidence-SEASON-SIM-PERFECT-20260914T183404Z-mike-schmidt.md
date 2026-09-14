# Failure evidence — `SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt`

## Verdict

Failed Perfect acceptance test. Do not treat as a passing season.

## Enrollment

- Enrollment: `rec2r1VgYEEWJBeKG`
- Athlete: `recRrd9nLKwK4vspy`
- Live Lifetime XP Earned: `4495`
- Live active XP sum (Active XP Points): `4495`
- Pre-restore snapshot (documented): `4950`
- Target: `4980`

## Active XP buckets

```json
{
  "Submission XP": 1340,
  "Homework XP": 700,
  "Video XP": 750,
  "Streak XP": 0,
  "Weekly Threshold XP": 450,
  "Perfect Week XP": 1000,
  "Shot Milestone XP": 165,
  "Zoom XP": 90
}
```

- Active events: 160; Inactive events: 9
- Inactive Streak XP events: 9

## Inactive STREAK_XP Source Keys

- `recTznj0JiKfdLQ0o` — `STREAK_XP|rec2r1VgYEEWJBeKG|rechOec7g8LBLcdgl|2027-04-29` (15 XP)
- `recf1vkdZ2ne9j7ZP` — `STREAK_XP|rec2r1VgYEEWJBeKG|recQuAtXyT2wKJNGI|2027-04-27` (10 XP)
- `recfAsDoPUfAe35tX` — `STREAK_XP|rec2r1VgYEEWJBeKG|recP8QP4uhEXaiZAX|2027-05-01` (20 XP)
- `recrVtuxkCAEwJdXk` — `STREAK_XP|rec2r1VgYEEWJBeKG|recxzySdFFaAOqNNG|2027-05-04` (30 XP)
- `recODbaVQBLttGBcJ` — `STREAK_XP|rec2r1VgYEEWJBeKG|recJ2caP3qBUfqzEp|2027-05-14` (50 XP)
- `rec4opM0btpNTu49z` — `STREAK_XP|rec2r1VgYEEWJBeKG|rechvtS1pfT086cwW|2027-05-24` (60 XP)
- `recHeoeHJZujHD3ET` — `STREAK_XP|rec2r1VgYEEWJBeKG|recewTtymiSN7Hkhw|2027-06-13` (90 XP)
- `recW2w2hgyrH6EsiE` — `STREAK_XP|rec2r1VgYEEWJBeKG|recgaun3HjV7EB2kN|2027-06-03` (75 XP)
- `rec6bwh6cDL2f1j3O` — `STREAK_XP|rec2r1VgYEEWJBeKG|recz5At8CvV5f4iFg|2027-06-23` (105 XP)

## Week 2 WAS

- WAS: `recYhbzze2Xc75lDa`
- Goal Completion %: `0`
- Threshold XP Status: `Processed`
- Requeue Threshold XP: `None`
- Expected missing 150 Source Key: `WEEKLY_THRESHOLD|rec2r1VgYEEWJBeKG|rec7RpUMVLbcrmn4h|150`
- Missing 150 key present in base: `False`
- Present WT keys for week: `['WEEKLY_THRESHOLD|rec2r1VgYEEWJBeKG|rec7RpUMVLbcrmn4h|100', 'WEEKLY_THRESHOLD|rec2r1VgYEEWJBeKG|rec7RpUMVLbcrmn4h|125']`

## Formula state

- Production-normal (no SEASON-SIM branches): `True`
- SEASON-SIM hits: `0`

## EHQ / email safety

- EHQ rows: `94`
- Recipients: `{'schmidt@fairfieldbasketballclub.com': 95}`
- Unsafe recipients: `NONE`
- Allowlist only: `True`

## Explicit statement

The 4,950 number was a pre-restore simulation snapshot (missing one 150% Weekly Threshold award = 30 XP vs target 4,980). The live active XP after Production-normal formula restore reflects post-restore ineligibility/deactivation (nine STREAK_XP events inactive when that state is present). Future-dated Week 2 WAS recYhbzze2Xc75lDa shows Goal Completion %=0 under Production NOW() formulas. Do not fabricate the missing 30-XP event and do not requeue under restored formulas. Treat this run as a failed acceptance test.

Machine-readable: `C:/Users/mschmidt_fairfield/Documents/GitHub/127si-shooting-challenge/docs/audits/readiness-20260914/failure-evidence-SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt.json`
