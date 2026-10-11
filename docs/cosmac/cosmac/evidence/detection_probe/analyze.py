"""Post-processes probe_results.json: recall, FPR, attribution, ablations (no re-scan)."""
import json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "probe_results.json")))
ACT = {"critical": "block", "high": "block", "medium": "flag", "low": "log"}
ORDER = ["block", "flag", "log", "pass"]
ML = {"d022_semantic_classifier"}
NON_REGEX = {"d022_semantic_classifier", "d028_sequence_alignment", "d027_stylometric_discontinuity", "d021_vault_similarity",
             "d033_topic_drift", "d035_perplexity_spectral", "d023_pii_detection"}


def short(d):
    return d.split("_")[0]


def action(dets):
    if not dets:
        return "pass"
    return min((ACT[d["sev"]] for d in dets), key=ORDER.index)


def base(r):
    return action(r["detections"])


def no_d022(r):
    return action([d for d in r["detections"] if d["id"] not in ML])


def d022_medium(r):
    return action([dict(d, sev="medium") if d["id"] in ML else d for d in r["detections"]])


def agree2(r):
    """block iff baseline would block AND (a regex-family detector of high/critical severity fires OR >=2 detectors fire)."""
    dets = r["detections"]
    a = action(dets)
    if a != "block":
        return a
    regex_block = any(d["id"] not in NON_REGEX and ACT[d["sev"]] == "block" for d in dets)
    return "block" if (regex_block or len(dets) >= 2) else "flag"


assert all(base(r) == r["action"] for r in R), "post-processing does not reproduce engine action"

att = [r for r in R if r["label"] == "attack"]
ben = [r for r in R if r["label"] == "benign"]
print(f"attacks={len(att)} benign={len(ben)}")

print("\n== Per attack type (baseline): blocked / flagged-only / passed")
for c in dict.fromkeys(r["category"] for r in att):
    xs = [r for r in att if r["category"] == c]
    k = Counter(r["action"] for r in xs)
    print(f"{c:22s} n={len(xs):2d} block={k['block']:2d} flag={k['flag']:2d} log={k['log']} pass={k['pass']:2d}  block-recall={k['block']/len(xs):.0%} any={1-k['pass']/len(xs):.0%}")
k = Counter(r["action"] for r in att)
print("ALL", dict(k), f"block-recall={k['block']/len(att):.1%} non-pass={(len(att)-k['pass'])/len(att):.1%}")

print("\n== Multi-step with conversation_history passed in context")
ms = [r for r in att if r.get("with_history")]
print(" no history:", dict(Counter(r["action"] for r in ms)))
print(" with history:", dict(Counter(r["with_history"]["action"] for r in ms)))
print(" detectors firing with history:", dict(Counter(short(d["id"]) for r in ms for d in r["with_history"]["detections"])))
print(" detectors firing w/o history:", dict(Counter(short(d["id"]) for r in ms for d in r["detections"])))

print("\n== Recall by style group")
def grp(s):
    for g in ("obvious", "paraphrase", "polite", "embedded", "non_english"):
        if s.startswith(g):
            return g
    return "other(encoded/indirect formats)"
for g in ["obvious", "paraphrase", "polite", "embedded", "non_english"]:
    xs = [r for r in att if grp(r["style"]) == g and r["category"] not in ("encoded_instructions",)]
    k = Counter(r["action"] for r in xs)
    print(f"{g:12s} n={len(xs):2d} block={k['block']} flag={k['flag']} pass={k['pass']} block-recall={k['block']/len(xs):.0%}")
print("encoded by scheme:")
for r in att:
    if r["category"] == "encoded_instructions":
        print(f"   {r['style']:16s} {r['action']:5s} {[short(d['id']) for d in r['detections']]}")

print("\n== Which detectors catch attacks")
print(" any-fire:", dict(Counter(short(d["id"]) for r in att for d in r["detections"]).most_common()))
blocked = [r for r in att if r["action"] == "block"]
solo = Counter(short(r["detections"][0]["id"]) for r in blocked if len(r["detections"]) == 1)
print(f" blocked attacks={len(blocked)}; single-detector blocks: {dict(solo)}")
only22 = [r for r in blocked if all(d["id"] in ML or ACT[d['sev']] != 'block' for d in r["detections"])]
print(f" blocked attacks where d022 is the ONLY block-capable detector: {len(only22)}/{len(blocked)}")
regex_hit = [r for r in att if any(d["id"] not in NON_REGEX and ACT[d["sev"]] == "block" for d in r["detections"])]
print(f" attacks with a block-capable regex-family hit: {len(regex_hit)}/{len(att)}")
d28 = [r for r in att if any(d['id'].startswith('d028') for d in r['detections'])]
print(f" attacks with d028 hit: {len(d28)}/{len(att)}")

print("\n== Benign FPR (baseline)")
for c in dict.fromkeys(r["category"] for r in ben):
    xs = [r for r in ben if r["category"] == c]
    k = Counter(r["action"] for r in xs)
    print(f"{c:20s} n={len(xs):2d} block={k['block']:2d} flag={k['flag']:2d} log={k['log']} pass={k['pass']:2d}  block-FPR={k['block']/len(xs):.0%}")
k = Counter(r["action"] for r in ben)
print("ALL", dict(k), f"block-FPR={k['block']/len(ben):.1%} non-pass-FPR={(len(ben)-k['pass'])/len(ben):.1%}")
nb = [r for r in ben if r["category"] != "short_fragment"]
k2 = Counter(r["action"] for r in nb)
print(f"excluding short fragments: n={len(nb)} block={k2['block']} ({k2['block']/len(nb):.1%}) flag={k2['flag']}")

print("\n== FP attribution")
fps = [r for r in ben if r["action"] == "block"]
sig = Counter("+".join(sorted(short(d["id"]) for d in r["detections"] if ACT[d["sev"]] == "block")) for r in fps)
print(" block-capable detector sets on blocked benign:", dict(sig.most_common()))
print(f" d022-alone blocks: {sum(1 for r in fps if [d['id'] for d in r['detections'] if ACT[d['sev']]=='block'] == ['d022_semantic_classifier'])}/{len(fps)}")
print(" all detectors firing on benign:", dict(Counter(short(d["id"]) for r in ben for d in r["detections"]).most_common()))
for r in ben:
    if r["action"] != "pass":
        print(f"   [{r['action']}] {r['category']:18s} {[(short(d['id']), d['conf']) for d in r['detections']]} :: {r['text'][:70]!r}")

print("\n== d022 short-input test")
def nwords(t): return len(t.split())
for lo, hi in [(1, 2), (3, 5), (6, 15), (16, 60), (61, 10**6)]:
    xs = [r for r in ben if lo <= nwords(r["text"]) <= hi]
    f = [r for r in xs if any(d["id"] in ML for d in r["detections"])]
    print(f" benign {lo}-{hi if hi<10**6 else '+'} words: d022 fires {len(f)}/{len(xs)}")
sf = [r for r in ben if r["category"] == "short_fragment"]
f = [r for r in sf if any(d["id"] in ML for d in r["detections"])]
print(f" short fragments d022 fired: {len(f)}/{len(sf)}; conf: {sorted(d['conf'] for r in f for d in r['detections'] if d['id'] in ML)}")
print("   passed fragments:", [r["text"] for r in sf if r["action"] == "pass"])

print("\n== Ablations (post-processed from per-detector results)")
print(f"{'variant':38s} {'attack block':>14s} {'attack non-pass':>16s} {'benign block':>14s} {'benign non-pass':>16s} {'benign block excl. short':>24s}")
for name, fn in [("baseline", base), ("(i) d022 disabled", no_d022), ("(ii) d022 severity=medium", d022_medium), ("(iii) block needs regex or >=2", agree2)]:
    a = Counter(fn(r) for r in att); b = Counter(fn(r) for r in ben); b2 = Counter(fn(r) for r in nb)
    print(f"{name:38s} {a['block']:3d}/{len(att)} {a['block']/len(att):5.1%} {len(att)-a['pass']:4d}/{len(att)} {(len(att)-a['pass'])/len(att):5.1%} "
          f"{b['block']:3d}/{len(ben)} {b['block']/len(ben):5.1%} {len(ben)-b['pass']:4d}/{len(ben)} {(len(ben)-b['pass'])/len(ben):5.1%} {b2['block']:6d}/{len(nb)} {b2['block']/len(nb):5.1%}")
print("\nper-attack-type block recall under ablations")
for c in dict.fromkeys(r["category"] for r in att):
    xs = [r for r in att if r["category"] == c]
    print(f" {c:22s} n={len(xs)} base={sum(base(r)=='block' for r in xs)} no_d022={sum(no_d022(r)=='block' for r in xs)} d022med={sum(d022_medium(r)=='block' for r in xs)} agree2={sum(agree2(r)=='block' for r in xs)}")

print("\n== d022 confidence distribution when it fires")
import statistics
ca = [d["conf"] for r in att for d in r["detections"] if d["id"] in ML]; cb = [d["conf"] for r in ben for d in r["detections"] if d["id"] in ML]
print(f" attacks n={len(ca)} min={min(ca):.3f} median={statistics.median(ca):.3f} | benign n={len(cb)} min={min(cb):.3f} median={statistics.median(cb):.3f}")
for th in (0.9, 0.99, 0.999, 0.9999):
    print(f"  d022 conf>={th}: attacks {sum(c>=th for c in ca)} benign {sum(c>=th for c in cb)}")

print("\n== Missed attacks (pass or flag-only)")
for r in att:
    if r["action"] != "block":
        print(f"   [{r['action']}] {r['category']:20s} {r['style']:14s} {[short(d['id']) for d in r['detections']]} :: {r['text'][:80]!r}")
