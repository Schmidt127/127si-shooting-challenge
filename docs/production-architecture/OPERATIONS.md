# Operations — troubleshooting first looks

**Status:** Authoritative (FUT-058 · 2026-09-15)

## Routine ops

1. Confirm git tip: `git fetch && git rev-parse origin/master`
2. Read [`../CURRENT-TRUTH.md`](../CURRENT-TRUTH.md) for overlays
3. Confirm Automation editor versions for the scripts you are debugging (not Automations-table Code alone)
4. Prefer disposable Schmidt enrollments for live tests; never blast real parents

## Failure playbooks

### Submission does not award XP

1. Submission: Count It / Reconciliation Needed? / Week / Enrollment linked  
2. Automation **010** run history  
3. XP Events for `SUBMISSION_XP|{submissionId}` (Active?)  
4. Competing duplicate XP rows / soft-skip conditions  

### Homework does not link

1. Submission Asset homework readiness fields  
2. Automation **020** (and **009** if assets missing — **009** is deployed v1.3 / SC-160)  
3. PHA / Week / Enrollment links on Homework Completion  
4. Reflection path uses **067**  

### Attachment does not transfer / upload stuck

1. Submission Asset Upload Status / Send to Make Trigger  
2. **070a** (homework) or **070b** (video) runs  
3. Make scenario + Lambda logs  
4. **022** writeback · **070c** verify (video)  
5. Canonical URL / Storage Key / hashes  

### Communication does not send

1. Email Handoff Queue: Status Ready? · Event Type · handoff key  
2. **079** run + Hub ingress logs  
3. Hub Message / Delivery Status · Send Block Reason formulas  
4. Test Allowlist · Suppressions · testMode  
5. Resend dashboard / webhook  

### Weekly summary does not build

1. WAS exists (**031**) · Grade Band (**030**) · Goal (**032**) · Homework (**033**)  
2. **118** / **072** / **119** / **074** chain  
3. Package fields + Ready?/Sent?  
4. Then Hub path as above  

### Level does not update

1. XP Events Active for enrollment  
2. **041** Level Recalc Needed  
3. **042** gates (Zoom / homework / etc.) blocking Next Level  
4. Level Gate Rules + Config  

### Achievement does not unlock

1. Streak: **053** occurrence → **054** / unlock path  
2. Perfect Week: **057** eligibility → **058** unlock → **059**  
3. Milestones: **066** → **059**  
4. Milestone Source Key uniqueness · Active? on unlock  

### Airtable / Make / webhook failure

1. Script `statusOut` / `errorOut` / `debugStep` outputs  
2. Input `recordId` still dynamic (not hardcoded)  
3. Make scenario ON/OFF (upload vs email — email should stay off)  
4. Secrets present in Airtable automation inputs / Vercel env (do not log values)  

## Safe testing reminders

- Email allowlist: Schmidt addresses only until Live cutover  
- Disposable-data mode excludes **Weeks** and schema/config  
- Do not trigger unintended production parent emails  
