# Project status and plan

`PROJECT_CONTEXT.md` and `ROADMAP.md` were **removed** in phase 0 (DOC-02).

Both were inherited from prompt-shield and had drifted badly out of date:

| File | Claimed | Actual at the time of removal |
|---|---|---|
| `PROJECT_CONTEXT.md` | version 0.1.0, 159 tests passing, last updated 2026-02-12 | version 0.8.1, 1,369 tests passing |
| `ROADMAP.md` | 22 detectors | 35 detectors |

Keeping two stale summaries alongside an authoritative specification is how
documentation drift happens, so they were deleted rather than rewritten.

## Where the current information lives

| What you want | Where it is |
|---|---|
| What COSMAC is, and what it does and does not claim | [`../README.md`](../README.md) |
| Target architecture, requirements, threat model | [`cosmac/cosmac/COSMAC_SPEC.md`](cosmac/cosmac/COSMAC_SPEC.md) |
| Delivery phases and milestones | `COSMAC_SPEC.md` section 12, [`cosmac/cosmac/COSMAC_BACKLOG.md`](cosmac/cosmac/COSMAC_BACKLOG.md) section 2 |
| The 215 stories, their order and dependencies | [`cosmac/cosmac/COSMAC_BACKLOG.md`](cosmac/cosmac/COSMAC_BACKLOG.md) |
| Interfaces and data contracts | [`cosmac/cosmac/COSMAC_INTERFACES.md`](cosmac/cosmac/COSMAC_INTERFACES.md) (draft v0.1) |
| Independent review of the specification | [`cosmac/cosmac/COSMAC_SPEC_REVIEW.md`](cosmac/cosmac/COSMAC_SPEC_REVIEW.md) |
| What phase 0 changed, and its test results | [`cosmac/PHASE_0_REPORT.md`](cosmac/PHASE_0_REPORT.md) |
| Licences for models, datasets and libraries | [`licences.md`](licences.md) |
| Release history, including the upstream's | [`../CHANGELOG.md`](../CHANGELOG.md) |

## Current position

Phase 0 (milestone M0) is the foundation: the rename, the inherited-defect
fixes, the evaluation harness and the two spikes. Phase 1 (M1 and M2) builds
the ingestion, canonicalisation, neutralisation and gateway components that
the specification describes; none of those exists yet.
