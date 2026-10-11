# SPK-01 — Performance spike

**Story:** SPK-01 (M0) &middot; **Implements:** NFR-3, review section 6.5
**Harness:** [`tools/spike_performance.py`](../../tools/spike_performance.py)
**Raw results:** [`evidence/spk01_results.json`](evidence/spk01_results.json)

A spike ends with a written result and a recommendation. Its code is not
merged into the product unless a follow-up story says so.

---

## Machine

Windows 11 / AMD64 / Python 3.12.2, CPU only, no GPU. **This is a developer
laptop, not reference hardware.** Decision 7 (reference CPU) is still open;
SPK-06 re-measures on whatever is chosen. Every figure below is in-process
scan latency with no network, no serialisation and no queueing — real server
latency will be higher.

## 1. Latency by NFR-3 length bucket

| Bucket | p50 (ms) | p95 (ms) | Candidate NFR-3 target | Meets it? |
|---|---|---|---|---|
| 0–500 | 163.9 | 170.9 | p95 ≤ 150 ms | **No** — 14% over |
| 501–2k | 673.8 | 700.6 | p95 ≤ 400 ms | **No** — 75% over |
| 2k–10k | 1,789.6 | 1,869.9 | (async path proposed > 8k) | — |
| 10k+ | 3,110.0 | 3,157.9 | (async path proposed > 8k) | — |

The spec recorded inherited in-process medians of 42–47 ms under 120
characters and 288 ms at 2,000. The figures here are higher at every size.
Two reasons, and the second is the important one:

1. This machine is slower than the one the spec's probe ran on.
2. **All 35 detectors are enabled here**, including `d035`
   (perplexity-spectral, 200 ms) which is opt-in and was off in the probe.

So these numbers are the *full-configuration* cost, not a regression.

## 2. Where the time goes

Per-detector p50 on a 2,000-character input:

| Detector | p50 (ms) | Share |
|---|---|---|
| `d022_semantic_classifier` | 531.9 | ~58% |
| `d035_perplexity_spectral` | 200.3 | ~22% |
| `d028_sequence_alignment` | 138.6 | ~15% |
| `d021_vault_similarity` | 29.8 | ~3% |
| `d025_multi_encoding` | 9.4 | ~1% |
| everything else (30 detectors) | < 4 each | ~1% |

**Three detectors account for roughly 95% of scan cost.** The other 32 are
effectively free. Any latency work that is not aimed at `d022`, `d035` or
`d028` is not worth doing.

## 3. `d028` sequence alignment grows superlinearly

| Input length | p50 (ms) | ms per 1k chars |
|---|---|---|
| 500 | 49.6 | 99.2 |
| 2,000 | 136.3 | 68.2 |
| 8,000 | 697.0 | 87.1 |
| 16,000 | 1,113.6 | 69.6 |

Smith-Waterman is O(*n*·*m*) against each stored attack sequence, and the
measured curve is consistent with that: a 32× input grows cost 22×. On a
16,000-character document `d028` alone costs 1.1 s.

**Recommendation: cap it.** A length cap on `d028` (proposal: 4,000
characters of canonical text per segment, applied per segment rather than
per document) bounds the worst case without losing the detector on the
segment sizes that matter, because phase 1 scans *segments*, not whole
documents. The cap belongs with the segment model in ING-01, not here.

## 4. Verdict cache

The engine has no verdict cache. A repeated identical scan costs the same as
the first (≈674 ms at 2k). That whole cost is what FR-44 recovers for
identical input. Worth building, but it does nothing for the first scan of
any given content, which is the case that matters for a gateway in the
request path.

## 5. What was NOT measured, and why

The story asks for a quantised or ONNX classifier comparison. **It was not
done.** Recorded here rather than estimated:

| Not measured | Why | Consequence |
|---|---|---|
| ONNX / quantised `d022` | Needs `optimum[onnxruntime]` and a conversion run | The targets below are for the PyTorch classifier as shipped. A 2–4× gain is *plausible* but unverified, and nothing may be planned on it. |
| Token-sized windows | `d022` already chunks; an alternative policy needs DET-04 (M2) | — |
| Cross-segment concatenated view | Does not exist until DET-05 (M2) | The spec's question "is cross-segment scanning affordable in line?" **cannot be answered yet.** |
| Detection change from quantisation | Depends on the above | EVL-02 must re-run if quantisation is adopted. |

## 6. Recommendation for NFR-3

**Do not fix NFR-3 targets from this spike.** Two of its inputs are missing
(reference hardware, ONNX measurement) and a third (cross-segment cost) is
unanswerable before M2.

What the data does support:

1. **The candidate targets are not met today** — 164 ms p95 against ≤ 150 ms
   at 0–500, and 701 ms against ≤ 400 ms at 501–2k, with everything enabled.
2. **Full windowing and cross-segment scanning are not affordable in line**
   at the current per-detector cost. A 2k scan already costs 674 ms;
   scanning a concatenated view multiplies that. The asynchronous path for
   documents is not optional — plan for it.
3. **The lever is `d022`.** It is 58% of cost on its own. If ONNX or
   quantisation does not deliver, the targets must move, not the design.
4. **`d035` should stay opt-in.** 200 ms for a detector that is off by
   default is fine; making it default would add 22% to every scan.
5. **Cap `d028`** as described above.

**Next:** SPK-06 (product owner) records the reference CPU and sets the
final targets. A follow-up story should do the ONNX conversion and re-run
this harness before those targets are fixed.
