# Prompt to start the next session

Copy everything inside the box below and paste it as your first message on
the new laptop, after unzipping the project and opening the
`prompt-shield` folder.

---

## ⚠️ Before you zip — two things that will break it

**1. INCLUDE the `.git` folder.**
It is hidden, and many zip tools skip hidden folders by default. Without it
you lose all 12 commits, every commit message, and the ability to see what
changed and why. **The project is nearly worthless without it.**

Check after unzipping on the new laptop:
```bash
git log --oneline | head -3
```
If that errors, the `.git` folder did not travel. Use
`cosmac-phase-0.bundle` instead (see `HANDOVER.md`).

**2. EXCLUDE the `.venv` folder.**
It is several gigabytes and it **will not work** on another machine —
virtual environments bake in absolute paths from the machine that made them.
Delete it before zipping and rebuild it on the new laptop. The prompt below
tells the assistant how.

---

## The prompt

```
I am continuing work on COSMAC, a prompt-injection defence tool. Phase 0 is
finished; I want to start the next phase. This project folder was moved from
another laptop, so nothing is set up yet.

START BY READING THESE, IN THIS ORDER:
  1. docs/cosmac/HANDOVER.md        - what exists, what is blocked
  2. docs/cosmac/PHASE_0_REPORT.md  - what phase 0 changed and its results
  3. docs/cosmac/cosmac/COSMAC_BACKLOG.md - the 215 stories, sections 2 and 5

Then do these three things in order, and report back before writing any
feature code:

STEP 1 - CONFIRM THE PROJECT ARRIVED INTACT
  - Run: git log --oneline | head -3
    Expect 12 commits, the newest being the handover docs commit.
    If git errors, the .git folder did not survive the zip: tell me, and use
    cosmac-phase-0.bundle instead.
  - Check whether .venv exists. If it does, delete it: it came from a
    different machine and will not work.

STEP 2 - REBUILD THE ENVIRONMENT
  - Create a fresh virtual environment on Python 3.10-3.13.
  - Install: pip install -e ".[dev,fastapi,mcp,observability,sentiment,language]"
    plus uvicorn (the REST API needs it and it is not a declared dependency).
  - If downloads are slow, use uv with UV_CONCURRENT_DOWNLOADS=50 - the last
    machine was throttled to about 25 MB/min by its connection, not by pip.
  - This takes a while. Torch and the models are large. Tell me the progress
    as you go rather than going quiet.

STEP 3 - VERIFY NOTHING BROKE IN TRANSIT
  Run these and show me the output:
    make guards
    make ci
    cosmac eval run --set docs/cosmac/evidence/probe_set_v1.jsonl --out eval-out

  It should reproduce EXACTLY:
    - tests: 1403 passed, 21 skipped, 0 failed
    - attack detection:  80.0% [72.0-86.2%] n=120
    - benign block rate: 27.5% [20.3-36.1%] n=120

  The first scan is slow (~10s) because it downloads the DeBERTa and MiniLM
  models. If any number differs, STOP and tell me - something about the
  environment is different and I do not want to build on it.

THEN, FOR THE NEXT PHASE:

The whole main line of phase 1 is blocked on DOC-01, a design-document
sign-off that needs an architect and a product owner, not code. ING-01 is
blocked, and everything downstream of it (DET-01, TRU-01, DEC-01, POL-01,
NEU-01, GW-01) is blocked behind that.

But SEVEN stories need no outstanding decision and can start now. Propose a
plan for these, in this order, and tell me which you would do first and why:

  DEF-06 (S) Replace the blanket long-input flag with a real resource check.
             Right now d026 flags ANY input over 10,000 characters as an
             attack, so a large benign document is treated as hostile.
  DEF-07 (S) Fix noisy patterns in d011, d012 and d023. Today a stylesheet
             link, indented Python, and an ordinary email address all
             trigger detections. This is the main cause of the 27.5% false
             positive rate.
  CAN-04 (S) Wire up the multi-encoding preprocessor. Phase 0 found it
             exists in cosmac/decoders/ but the engine never calls it,
             despite the old README advertising it.
  CAN-03 (S) Add the missing invisible-character classes: bidirectional
             controls, Unicode tags, variation selectors, ANSI escapes.
  SVC-01 (S) API-key authentication on every route except health probes.
  SVC-03 (M) Fail closed on detector error, timeout and model-load failure.
  SVC-05 (M) One detector runner on a shared pool, bounded queue.

RULES I WANT YOU TO FOLLOW - these come from the project's own standards:

  - Every story has acceptance criteria in COSMAC_BACKLOG.md section 5.
    Read them and meet them. Do not invent your own.
  - A bug fix needs a test that FAILS BEFORE the fix. Write it first.
  - If you change detection behaviour, run the evaluation command before and
    after and show me both sets of figures. Attack recall must not fall by
    more than 2 points.
  - Never quote a percentage without its confidence interval and sample
    count. The project treats a bare percentage as not a result.
  - The 240-sample probe set is an internal development set written by one
    person. It is not a gate and supports no quality claim.
  - Do not add a git 'origin' remote and do not publish anything. That is
    blocked until decision 14 (who owns the repository and package name) is
    made. The release workflow's publishing step is deliberately disabled.
  - Verify things in the code rather than trusting the documentation. Phase 0
    found two documented features that did not exist and one "bug" that was
    only a dependency version bound.

Work through one story at a time. Show me the plan before you start coding.
```

---

## What to tell the person receiving this

If someone else is picking the project up, they also need:

1. **The zip** (with `.git`, without `.venv`) — or `cosmac-phase-0.bundle`.
2. **The Phase 0 report** — either the private artifact link shared from its
   own Share menu, or just `docs/cosmac/PHASE_0_REPORT.md`, which has the
   same content and travels with the folder.
3. **Answers to the blockers** in `HANDOVER.md` section 6, if they have them.
   Two of those (naming the evaluation author, and the DOC-01 sign-off) block
   more work than all the coding tasks combined.
