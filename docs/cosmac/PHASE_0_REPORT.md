# COSMAC phase 0 — completion report

**Milestone:** M0 (Foundation) &middot; **Spec phase:** 0
**Branch:** `phase-0-foundation` &middot; **Base:** `upstream-v0.8.1`
**Date:** 2026-10-11

---

## 1. Summary

All **25 M0 stories** are implemented. The suite is green, every static
check passes, and both spikes have reported with recommendations.

| Measure | Baseline | Final | Change |
|---|---|---|---|
| Tests passed | 1,369 | **1,403** | +34 |
| Tests failed | 0 | **0** | — |
| Skipped | 19 | 21 | +2 |
| `ruff check` | clean | **clean** | — |
| `ruff format --check` | clean (264) | **clean (284)** | — |
| `mypy src/` | clean | **clean (137 files)** | — |
| Old-name guard | n/a | **clean** | new |
| Version-sync guard | n/a | **clean** | new |

10 commits, 422 files changed, 145 source files touched.

**One thing M0 does not deliver:** DOC-01 cannot be closed by engineering.
It needs an architect's sign-off on the interfaces document and a product
owner's approval of three of its sections. The review *package* is ready;
the signatures are not. See section 6.

---

## 2. What changed, by story

### Repository and rename (REP)

| Story | What was done | Evidence |
|---|---|---|
| REP-01 | Test baseline captured with provenance header | `evidence/test_baseline.txt` |
| REP-02 | `NOTICE` with derivation, change summary, trademark and benchmark disclaimers | `NOTICE` |
| REP-03 | Upper bounds on all 28 dependencies; `mcp>=1.10,<2` | `pyproject.toml` |
| REP-04 | No forced coverage report; `slow`/`network`/`model` markers; session-wide data-dir redirect | `pyproject.toml`, `tests/conftest.py` |
| REP-05 | Rename manifest and dry-run script | `tools/rename_manifest.yaml`, `evidence/rename_dryrun.txt` |
| REP-06 | **The rename commit** — 2,065 lines across 325 files | commit `65e000c` |
| REP-07 | Old-name check, wired into CI as its own job | `tools/check_old_names.py` |
| REP-08 | Upstream feed URLs emptied; canary secret generated per install | `canary/watermark.py`, `config/default.yaml` |
| REP-09 | Single version source; Docker and Helm brought into line | `tools/check_version_sync.py` |
| REP-10 | Dify, n8n and PyPI-alias plugins removed from the build | commit `65e000c` |
| REP-11 | `make setup` / `make ci` from a clean clone, as a CI job | `Makefile`, `.github/workflows/ci.yml` |

The rename covered the import package, distribution, four console scripts,
environment prefix, data paths, config root, logger root and metric prefix.
**Three middleware classes that shared the single name
`PromptShieldMiddleware`** now have distinct names:

```
fastapi_middleware.PromptShieldMiddleware -> CosmacASGIMiddleware
flask_middleware.PromptShieldMiddleware   -> CosmacFlaskMiddleware
django_middleware.PromptShieldMiddleware  -> CosmacDjangoMiddleware
```

Unchanged, as spec 9.1 requires: detector IDs `d001`–`d035`, the four MCP
tool names, the ChromaDB collection name, and model identifiers. The guard
asserts these survived.

### Inherited-defect fixes (DEF)

| Story | Defect | Fix |
|---|---|---|
| DEF-01 | Three learning loops on by default; `sync_threats()` fell back to the **unverified** path with only a `FutureWarning` | All three off (FR-45); unverified sync now **raises** |
| DEF-02 | Allowlist used `search()`, so `hello` allowed `hello. Ignore all previous instructions`; applied to retrieved content | `fullmatch()`; never applies to `retrieved`, `tool_description`, `memory` or the `tool_result` gate |
| DEF-03 | FastAPI, Flask and Django middleware forwarded an **unparseable body to the application unscanned** | All three refuse with 4xx; `allow_unparsed=True` opts out |
| DEF-04 | Five config keys nothing read; `COSMAC_LOGGING_LEVEL` set a dead key while the API read a different name | Dead keys removed; one `COSMAC_LOG_LEVEL` that actually configures logging; unknown keys rejected |
| DEF-05 | Release workflow published on a tag **with no test job** | Build requires test+lint+types+guards; publishing disabled pending decision 14 |

DEF-01, DEF-02 and DEF-03 are each a way past the scanner. They are the
security substance of phase 0.

### Evaluation harness (EVL)

| Story | Delivered |
|---|---|
| EVL-01 | Sample schema on the INT §1 vocabulary, loader, independence checker; probe set converted to 240 validated samples |
| EVL-02 | Wilson intervals, evaluation runner, report writer, `cosmac eval run` / `cosmac eval check` |
| EVL-03 | First reliability report on the shipped default, committed with raw results |
| EVL-04 | Licence register; PyMuPDF recorded **not permitted** |
| EVL-08 | CI regression job, report-only, posting the change from the merge base |

Every rate COSMAC publishes is a `Proportion` — observed value, 95% Wilson
interval and denominator. `Proportion.format()` *cannot* render a bare
percentage. The evaluation command **exits non-zero** if the classifier is
enabled but did not load, so a silently-absent classifier cannot be mistaken
for a clean sweep.

### Spikes and documentation

| Story | Outcome |
|---|---|
| SPK-01 | Performance spike reported — see section 4 |
| SPK-02 | Classifier benchmark reported — see section 5 |
| DOC-01 | Review package ready; **not signed off** — see section 6 |
| DOC-02 | README rewritten; two false claims corrected; stale files removed |

---

## 3. First reliability report (EVL-03)

Run on the shipped default configuration, commit `43c8d30`, against the
240-sample relabelled probe set.

| Measure | Result | Review predicted |
|---|---|---|
| Attack detection, overall | **80.0%** [72.0–86.2%] n=120 | 75–86% ✓ |
| Benign block rate | **27.5%** [20.3–36.1%] n=120 | 25–30% ✓ |

Both figures fall inside the ranges the independent review predicted, which
is the first evidence that the harness measures what it claims to.

Per attack type:

| Attack type | Detection |
|---|---|
| `instruction_override` | 100.0% [77.2–100.0%] n=13 |
| `encoded_instruction` | 93.8% [71.7–98.9%] n=16 |
| `context_poisoning` | 92.3% [66.7–98.6%] n=13 |
| `role_change` | 92.3% [66.7–98.6%] n=13 |
| `secret_extraction` | 92.3% [66.7–98.6%] n=13 |
| `indirect_injection` | 71.4% [45.4–88.3%] n=14 |
| `credential_theft` | 61.5% [35.5–82.3%] n=13 |
| `multi_step` | 58.3% [32.0–80.7%] n=12 |
| `tool_abuse` | 53.8% [29.1–76.8%] n=13 |

> **A 27.5% benign block rate is not a product.** The D1 gate is ≤5% and the
> D2 gate is ≤0.4%. The weakest types — tool abuse, multi-step, credential
> theft — are exactly the content-borne and cumulative attacks phase 1 and
> phase 2 are designed to address.

**What this figure is not:** it is a 240-sample internal development set
written by one author. It is not sealed, not independent, not in-domain, and
it supports no D1 claim. No spec §10.4 gate is met.

---

## 4. SPK-01 — performance

Measured on a developer laptop (Windows 11 / AMD64 / Python 3.12.2), all 35
detectors enabled. **Not reference hardware** — decision 7 is open.

Three detectors are ~95% of scan cost on a 2,000-character input:

| Detector | p50 (ms) | Share |
|---|---|---|
| `d022_semantic_classifier` | 531.9 | ~58% |
| `d035_perplexity_spectral` | 200.3 | ~22% |
| `d028_sequence_alignment` | 138.6 | ~15% |
| all 32 others | < 4 each | ~1% |

`d028` grows superlinearly — 49.6 ms at 500 chars to 1,113.6 ms at 16,000.
**Recommendation: cap it** at the segment level in ING-01.

Candidate NFR-3 targets are **not met today**: 170.9 ms p95 against ≤150 ms
at 0–500, and 700.6 ms against ≤400 ms at 501–2k.

**ONNX / quantisation was not measured.** It needs `optimum[onnxruntime]`
and a conversion run. Recorded as unmeasured rather than estimated, so
**NFR-3 targets must not be fixed from this spike**. Full details and the
cross-segment question (unanswerable before M2) are in
[`SPK-01_performance.md`](SPK-01_performance.md).

---

## 5. SPK-02 — classifier benchmark (decision 9)

| Candidate | Recall | Benign block rate |
|---|---|---|
| **inherited** (deberta-v3 prompt-injection-v2) | 65.0% [56.1–72.9%] | 18.3% [12.4–26.2%] |
| protectai v1 | 36.7% [28.6–45.6%] | 16.7% [11.1–24.3%] |
| deepset | **97.5%** [92.9–99.1%] | **47.5%** [38.8–56.4%] |

**No off-the-shelf candidate is close to D2.** The best recall available
flags nearly half of ordinary text. The lowest false-positive rate comes
with 36.7% recall.

**Recommendation: do not decide yet.** Recall at a fixed 1% benign block
rate was *not* measured — it needs a threshold sweep, and it is the one
thing that would reorder this table. `deepset`'s 97.5% recall says the
signal is there and the operating point is wrong, not the model.

**Answer to the spike's second question — are the D2 targets reachable?**
Not by swapping models. Closing the gap needs retraining on in-domain data,
a calibrated decision stage (FR-25) and probably the second stage in FR-26.
This confirms the spec's own highest-rated risk and should reach the product
owner before decision 11.

---

## 6. What phase 0 did NOT close

| Item | Status | Owner |
|---|---|---|
| **DOC-01 sign-off** | Review package ready; INT stays at **draft v0.1**. **ING-01 is blocked.** | Architect + PO |
| **Evaluation author** (decision 5) | **Still unnamed.** No M2 test-set story can start. | PO |
| **Team size / hackathon date** (decision 13) | Unset. M1 has no schedule. | PO |
| Decision 9 (classifier) | Deferred pending the threshold sweep | DS + PO |
| Decision 7 (reference CPU) | Open; SPK-06 | PO |
| Decision 11 (thresholds) | Open; due phase 1 exit | PO + customer |
| Decision 14 (ownership) | Open; **publishing stays disabled** | PO |
| Review problem **N7** | **Unresolved.** The benign-denominator conflict is EVL-07 (M1). Phase 0 did not settle it. | — |
| Model revision pinning | Not done; models fetch current revision on first use | — |
| Licence confirmations | Every model and dataset is **"not confirmed"** | PO |

---

## 7. Findings worth escalating

**1. The home-directory write is confirmed, not inferred.** Spec §5.7 listed
it as suspected. During the baseline run, `~/.cosmac/vault/chroma.sqlite3`
and the scan-history database were written *while the suite was running*,
timestamped at 15:16 and 15:17. Evidence in
`evidence/rep04_home_writes.txt`. Fixed by a session-wide redirect.

**2. Two documented capabilities do not exist.** Both were advertised in the
README:

- **`/metrics` is not served.** Zero references in `api.py`.
- **The multi-encoding preprocessor is not wired into the engine.** Zero
  references to `decoders` in `engine.py`.

Both are now stated as limitations, with a test that fails if the `/metrics`
claim returns.

**3. The MCP defect is a dependency bound, not a code bug.** The register
said the server was "broken on a fresh install, 13 tests fail". With
`mcp>=1.10,<2` installed, **all 18 MCP tests pass** with no code change.
Unbounded `mcp>=1.10` resolves to 2.x, which breaks the API.

**4. Three inherited tests encoded defects as requirements.** They were
updated, not deleted:

- `test_allowlist` asserted that the prefix `^safe:` allowed
  `"safe: test input ignore previous instructions"` — the bypass itself.
- `test_empty_body_passthrough` was misnamed: it sent `b"not json"` and
  asserted it passed through unscanned.
- The `sync_threats` transitional test asserted the `FutureWarning`
  fall-back; its own docstring said v0.8.0 would make it an error.

**5. Phase 0 introduced a CI-breaking format regression, now fixed.** At
`upstream-v0.8.1` `ruff format --check` was clean across 264 files; the
rename changed line lengths and broke 18. Caught by comparing against the
baseline rather than assuming the failures were pre-existing.

---

## 8. M0 exit checklist (backlog §7.2)

| Criterion | Status |
|---|---|
| REP-01 to REP-11 done; old-name check passes in CI | ✅ |
| Lint and type check clean; tests no worse than baseline | ✅ 1,403 vs 1,369, zero failures |
| Learning loops off; allowlist and parse-failure fixes merged | ✅ DEF-01, DEF-02, DEF-03 |
| `cosmac eval run` produces a report; first report committed | ✅ `evidence/report_v1/` |
| Regression job posts figures on every pull request | ✅ `regression.yml` |
| SPK-01 and SPK-02 have written results with recommendations | ✅ |
| Licence register exists | ✅ `docs/licences.md` |
| **INT at version 1.0** | ❌ **draft v0.1 — needs architect and PO** |
| Nothing published to any index or registry | ✅ publishing disabled |

**9 of 10 met. The outstanding item is a signature, not an implementation.**

---

## 9. Recommended next actions

1. **Name the evaluation author** (decision 5). Every M2 test-set story is
   blocked until this happens, and it is the most likely cause of a late M2.
2. **Hold the DOC-01 review.** Architect accepts the INT sections; PO
   approves 4.1, 4.2 and 10. This unblocks ING-01.
3. **State team size and the hackathon date** (decision 13), so the backlog
   order becomes a schedule.
4. **Run the classifier threshold sweep** before deciding decision 9.
5. **Escalate the D2 feasibility finding** from SPK-02 ahead of decision 11.
6. **Confirm the licences** in `docs/licences.md`. ING-07 is blocked until a
   PDF library is cleared; PyMuPDF is not permitted.

---

## 10. Evidence index

| Artefact | Path |
|---|---|
| Baseline test run | `evidence/test_baseline.txt` |
| Baseline without mcp (superseded) | `evidence/test_baseline_no_mcp.txt` |
| Post-fix run | `evidence/test_after_fixes.txt` |
| **Final verification run** | `evidence/test_final.txt` |
| Rename dry run / applied | `evidence/rename_dryrun.txt`, `evidence/rename_applied.txt` |
| Home-write evidence | `evidence/rep04_home_writes.txt` |
| Evaluation sample set | `evidence/probe_set_v1.jsonl` |
| First reliability report | `evidence/report_v1/report.md`, `results.json` |
| SPK-01 raw / write-up | `evidence/spk01_results.json`, `SPK-01_performance.md` |
| SPK-02 raw / write-up | `evidence/spk02_results.json`, `SPK-02_classifier_benchmark.md` |
| INT review package | `INT_REVIEW_RECORD.md` |
| Licence register | `../licences.md` |

Reproduce the headline figures:

```bash
make guards                                  # REP-07 and REP-09
make ci                                      # lint, types, guards, tests
cosmac eval run --set docs/cosmac/evidence/probe_set_v1.jsonl --out eval-out
```
