# SPK-02 — Classifier benchmark

**Story:** SPK-02 (M0) &middot; **Implements:** FR-27, **decision 9**
**Harness:** [`tools/spike_classifier_benchmark.py`](../../tools/spike_classifier_benchmark.py)
**Raw results:** [`evidence/spk02_results.json`](evidence/spk02_results.json)

Three candidates, one sample set, one command. The point of the spike is that
decision 9 (retrain the inherited classifier, or replace it) should rest on
one comparable table rather than on published figures from three different
papers measured on three different sets.

---

## Sample set

The 240-sample relabelled probe set (120 attack / 120 benign), EVL-01 schema,
fully independent by payload. **It is an internal development set written by
one author.** It is not sealed, not in-domain, and not a gate. Intervals at
n=120 are wide and are shown with every figure.

## Results

| Candidate | Recall | Benign block rate | p50 (ms) | Licence |
|---|---|---|---|---|
| **inherited** `protectai/deberta-v3-base-prompt-injection-v2` | 65.0% [56.1–72.9%] | 18.3% [12.4–26.2%] | 66.8 | Apache-2.0 (claimed, **not confirmed**) |
| `protectai/deberta-v3-base-prompt-injection` (v1) | 36.7% [28.6–45.6%] | 16.7% [11.1–24.3%] | 66.7 | Apache-2.0 (claimed, **not confirmed**) |
| `deepset/deberta-v3-base-injection` | **97.5%** [92.9–99.1%] | **47.5%** [38.8–56.4%] | 66.7 | MIT (claimed, **not confirmed**) |

Confusion matrices (tp / fn / fp / tn):

| Candidate | tp | fn | fp | tn |
|---|---|---|---|---|
| inherited | 78 | 42 | 22 | 98 |
| protectai-v1 | 44 | 76 | 20 | 100 |
| deepset | 117 | 3 | 57 | 63 |

Latency is indistinguishable across the three — same architecture, same size.
**Latency is not a differentiator here.**

## What this says

**1. No candidate is close to the D2 target.** D2 asks for ≥90% per attack
type at ≤0.4% in-domain benign block rate. The best recall on offer (97.5%)
comes with a **47.5% benign block rate** — it flags nearly half of ordinary
text. The lowest benign block rate on offer (16.7%) comes with 36.7% recall.
The gap to D2 is not a tuning gap.

**2. The inherited classifier is the best of the three on balance**, but not
by much, and its 65% recall at 18.3% false positives is not a product. Note
this measures `d022` alone; the *engine* reached 80.0% recall at 27.5% benign
block (EVL-03), because the other 34 detectors contribute.

**3. `protectai-v1` is strictly worse than the v2 it was superseded by** —
lower recall at a comparable false-positive rate. It is included as a floor,
and it confirms the incumbent is at least the better of its own lineage.

**4. `deepset` is not unusable — it is untuned.** 97.5% recall says the
signal is there. A 47.5% benign block rate at its *default* threshold says
the operating point is wrong, not the model. This is the most interesting
result in the table.

## Limits of this spike — read before quoting it

- **Recall at a fixed 1% benign block rate was NOT measured.** The story asks
  for it. It needs score outputs and a threshold sweep per candidate; the
  harness runs each at its own default threshold. Until that sweep is done,
  these numbers compare three arbitrary operating points, not three models.
  **This is the single biggest caveat and it changes the ranking.**
- **NotInject was not run.** Licence not confirmed (EVL-04), so it may not be
  used yet. The hard-benign picture is therefore missing.
- **n=120 per class.** Every interval spans 8–18 points. Differences smaller
  than that are noise.
- **Licences are as claimed on each model card and are not confirmed.** No
  candidate may be adopted until EVL-04 clears it.
- Only three candidates. The story asks for "at least three"; it is the
  minimum, not a survey.

## Recommendation for decision 9

**Do not decide yet. Run the threshold sweep first.** That is a days-sized
piece of work and it is the one thing that would change this table.

Beyond that, the evidence supports:

1. **Keep the inherited classifier for now.** It is the best balanced
   candidate measured, and nothing here justifies the cost of switching.
2. **Treat `deepset` as the leading replacement candidate**, conditional on
   the sweep. If it reaches useful recall at a 1% benign block rate, it
   outperforms the incumbent decisively. If it does not, it is out.
3. **Plan for retraining, not just selection.** No off-the-shelf candidate
   reaches D2. The gap between 65% recall at 18% FP and 90% per type at 0.4%
   FP will not close by swapping weights. This matches the spec's own
   high-likelihood risk that the D2 targets are not reached.
4. **Re-run on in-domain data before committing.** Benign block rate is the
   binding constraint, and it is the figure most sensitive to what "benign"
   looks like in the customer's traffic. Blocked on decision 12.

## Answer to the spike's second question

> *"…and a statement on whether the D2 targets look reachable."*

**Not with an off-the-shelf classifier.** On this set, reaching D2 means
simultaneously raising recall above 90% per type and cutting the benign block
rate to 0.4%. The candidates sit at 37–65% recall with 17–18% false
positives, or 97.5% recall with 47.5% false positives. Reaching D2 requires
retraining on in-domain data, a calibrated decision stage (FR-25), and
probably the second stage in FR-26 — not a model swap.

This should be raised with the product owner before phase 1 exit, when
decision 11 (acceptance thresholds) is made.
