# INT review record — DOC-01

**Story:** DOC-01 (M0) &middot; **Owner:** Technical solution architect
**Reviews:** `COSMAC_INTERFACES.md` draft v0.1
**Implements:** review problems N1, N2, N3

---

## Status: NOT SIGNED OFF

> **This story cannot be closed by engineering.** DOC-01 requires two named
> human approvals that no implementation can supply:
>
> 1. The **technical solution architect** accepts or changes each INT section
>    and raises the version to 1.0.
> 2. The **product owner** approves INT 4.1 (canonical forms), INT 4.2
>    (quarantine defaults) and INT 10 (measurement definitions).
>
> What phase 0 delivers is everything up to those signatures: the section
> inventory below, the stability marking that dependent stories need, the
> answers to the Appendix C points that concern INT, and the one INT section
> that phase 0 actually implemented and can therefore report on from code.
>
> **INT remains at draft v0.1.** Stories that depend on it may start only on
> sections marked *stable* below.

---

## 1. Section inventory and stability marking

Marking rule used: a section is **stable** when phase 0 either implemented it
or verified it needs no decision; **needs decision** when an open decision or
Appendix C assumption changes it; **draft** otherwise.

| INT section | Subject | Marking | Note |
|---|---|---|---|
| 1 | Vocabulary (`SourceType`, `TrustTier`, `Band`, `Action`, `AttackFamily`, `Capability`) | **stable** | Implemented verbatim in `evaluation/schema.py` (EVL-01). No conflict found. |
| 2 | Document and segment model | draft | Architect review outstanding (review problem N2). |
| 2.1 | Location values | draft | Depends on the offset map; SPK-03 reports in phase 2. |
| 3 | Ingestion and format sniffing | draft | TRU-02 in M1. |
| 4.1 | Canonical forwarded form | **needs decision** | PO approval required. Appendix C #2 and #4 both bear on it — see section 3. |
| 4.2 | Quarantine defaults | **needs decision** | PO approval required. Appendix C #4, #5, #7. |
| 4.3 | Isolation markers | draft | Effectiveness unmeasured until SPK-04 (phase 2). Defence in depth only. |
| 5 | Span confidence and `unmapped` | draft | SPK-03 decides the three values. |
| 7.6 | Error codes | draft | `rate_limited` referenced by DEF-09 (M2). |
| 10 | Measurement definitions | **needs decision** | PO approval required. Phase 0 implemented the parts it could — see section 2. |
| 11 | Session limits | draft | Appendix C #9. |

---

## 2. INT 10 — what phase 0 implemented and can report

EVL-02 is the one INT section phase 0 turned into running code, so it is the
one the architect can review against behaviour rather than intent.

**Implemented** (`src/cosmac/evaluation/metrics.py`, `runner.py`):

- Every published rate is a `Proportion`: observed value, 95% Wilson score
  interval, and denominator. `Proportion.format()` cannot render a bare
  percentage — the interval and `n=` are not optional.
- Wilson rather than the normal approximation, because at rates near 0 or 1
  with small `n` the normal approximation produces bounds outside [0, 1].
  Tested against the value the story names: 7 of 13 → 29%–77%.
- Independence is counted over payload ID and carrier ID (spec 10.1), and the
  report states independent payloads and carriers alongside the raw count.
- The report header carries commit, configuration hash, sample-set SHA-256,
  model identifiers and the machine. A figure without provenance is not
  emitted.
- The run **exits non-zero** if `d022` is enabled but did not load, so a
  silent "nothing detected" sweep cannot be mistaken for a clean result.

**Not implemented in phase 0, and why:**

| INT 10 definition | Status | Blocked on |
|---|---|---|
| `content preserved` | not implemented | Needs the neutraliser (NEU-01, M1) |
| `neutralised` | not implemented | Needs labelled spans + neutraliser; EVL-07 (M1) |
| `no garbled output` | not implemented | Same |
| Benign-block denominator rule (N7) | **not resolved** | EVL-07 carries it; see section 3 |

---

## 3. Appendix C points that concern INT

DOC-01 requires each to be answered in the review. Engineering's reading is
recorded; **none of these is a decision — each still needs the named owner.**

| # | Point | Engineering reading | Owner |
|---|---|---|---|
| 2 | M1 removes the whole segment, coarser than INT 4.1 sentence granularity | Accept for M1. It avoids the offset map, at the cost of removing benign text around an injection. INT 4.1 should record M1 granularity as an explicit, temporary deviation rather than be loosened. | TSA + PO |
| 4 | Source code quarantined by default (FR-33) vs sanitised in place (decision 3) | The reconciliation in the backlog is sound: quarantine is the default; sanitise-in-place is an operator opt-out by removing `source_code` from the quarantine list. INT 4.1 and 4.2 already carry both and do not conflict. | PO |
| 5 | "Contract" is a class a route declares; COSMAC does not recognise contracts | Accept. It makes FR-33 testable. The residual risk — an undeclared contract is handled as an ordinary document — belongs in DOC-07. | PO |
| 7 | M1 withholds email attachments; Word comments/tracked changes not forwarded at D1 | Accept. Both follow from "never passed through unscanned". Must be stated in the M1 claims sheet, since it reduces what the model receives. | PO |
| 11 | OCR noise adds a second INT 10 criterion: detection within 10 points of clean | The 10-point figure is a proposal with no measurement behind it. Recommend *not* writing it into INT 10 until ING-14 has data. | DS + PO |
| 15 | Evaluation command named `cosmac eval run` | **Implemented as proposed.** The inherited `benchmark` CLI commands are left in place for now; EVL-08 decides whether they are wired to the regression job or removed. | PO |

**Unresolved and material: review problem N7.** The conflict in the benign
denominator — whether a quarantined benign document counts in the benign
block rate, in content preserved, or both — is assigned to EVL-07 (M1), not
phase 0. Phase 0 did **not** resolve it, and the phase 0 report must not be
read as having done so.

---

## 4. What the architect still has to do

1. Accept or change INT sections 2, 2.1, 3, 4.3, 5, 7.6, 11.
2. Raise INT to version 1.0 in the same pull request.
3. Obtain PO approval for 4.1, 4.2 and 10, and link it from EVL-07.
4. Answer Appendix C #2, #4, #5, #7, #11 as decisions rather than readings.

Until step 2, every INT version reference in code comments and docs points at
**draft v0.1**, and ING-01 (which depends on DOC-01) may not start.

---

*Record produced during phase 0. It is a review package, not a review.*
