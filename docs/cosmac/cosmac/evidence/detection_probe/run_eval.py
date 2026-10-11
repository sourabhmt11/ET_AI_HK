"""Runs bundled sample benchmark, probe set, and latency. Writes raw per-sample results."""
import json, os, statistics, sys, time, logging, platform

logging.disable(logging.WARNING)
HERE = os.path.dirname(os.path.abspath(__file__))
from prompt_shield import PromptShieldEngine, __version__

CFG = {"prompt_shield": {"vault": {"enabled": False}, "history": {"enabled": False}, "feedback": {"enabled": False},
                         "logging": {"level": "ERROR"}}}
try:
    eng = PromptShieldEngine(config_dict=CFG)
except Exception as e:  # fall back to exactly what the lead specified
    print("fallback cfg", e)
    eng = PromptShieldEngine(config_dict={"prompt_shield": {"vault": {"enabled": False}}})

t = time.perf_counter(); eng.scan("warm up the classifier"); print("first scan s", round(time.perf_counter() - t, 2))
print("version", __version__, platform.platform(), platform.processor())
print("detectors enabled:", sum(1 for d in eng.list_detectors()))


def scan(text, ctx=None):
    t0 = time.perf_counter()
    r = eng.scan(text, context=ctx)
    ms = (time.perf_counter() - t0) * 1000
    return {"action": r.action.value, "risk": r.overall_risk_score, "ms": ms,
            "detections": [{"id": d.detector_id, "conf": round(d.confidence, 4), "sev": d.severity.value} for d in r.detections]}


# ---- bundled sample
from prompt_shield.benchmarks.datasets import load_dataset
samples = load_dataset("sample")
out = []
for s in samples:
    res = scan(s.text)
    out.append({"text": s.text, "is_injection": s.is_injection, **res})
json.dump(out, open(os.path.join(HERE, "bundled_results.json"), "w"), indent=1, ensure_ascii=False)
for name, pos in (("non-pass counts as positive (upstream definition)", lambda a: a != "pass"), ("block only", lambda a: a == "block")):
    tp = sum(1 for o in out if o["is_injection"] and pos(o["action"])); fn = sum(1 for o in out if o["is_injection"] and not pos(o["action"]))
    fp = sum(1 for o in out if not o["is_injection"] and pos(o["action"])); tn = sum(1 for o in out if not o["is_injection"] and not pos(o["action"]))
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    print(f"BUNDLED [{name}] n={len(out)} TP={tp} FN={fn} FP={fp} TN={tn} P={p:.3f} R={r:.3f} F1={(2*p*r/(p+r) if p+r else 0):.3f} FPR={fp/(fp+tn):.3f}")

# ---- probe
rows = [json.loads(l) for l in open(os.path.join(HERE, "probe.jsonl"))]
res = []
for r in rows:
    o = dict(r)
    o.update(scan(r["text"]))
    if r.get("history"):
        h = scan(r["text"], {"conversation_history": r["history"]})
        o["with_history"] = h
    res.append(o)
json.dump(res, open(os.path.join(HERE, "probe_results.json"), "w"), indent=1, ensure_ascii=False)

# ---- latency
def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]

short = [r["text"] for r in rows if len(r["text"]) < 120][:60]
lat_s = [scan(t)["ms"] for _ in range(3) for t in short]
long_text = (rows[-20]["text"] + " ") * 40
doc = " ".join(r["text"] for r in rows if r["category"] == "long_document")
doc = (doc * 3)[:10000]
lat_l = [scan(doc)["ms"] for _ in range(25)]
lat = {"short_n": len(lat_s), "short_p50": pct(lat_s, .5), "short_p95": pct(lat_s, .95), "short_mean": statistics.mean(lat_s),
       "long_chars": len(doc), "long_n": len(lat_l), "long_p50": pct(lat_l, .5), "long_p95": pct(lat_l, .95)}
# per-detector timing on the long doc, sequential
per = {}
from prompt_shield.config import get_detector_config
ctx = {"original_text": doc}
for d in eng._registry.list_all():
    if not get_detector_config(eng._config, d.detector_id).get("enabled", True):
        continue
    ts = []
    for _ in range(3):
        t0 = time.perf_counter(); d.detect(doc, context=ctx); ts.append((time.perf_counter() - t0) * 1000)
    per[d.detector_id] = round(statistics.median(ts), 2)
lat["per_detector_ms_long"] = dict(sorted(per.items(), key=lambda kv: -kv[1])[:8])
per = {}
for d in eng._registry.list_all():
    if not get_detector_config(eng._config, d.detector_id).get("enabled", True):
        continue
    ts = []
    for _ in range(5):
        t0 = time.perf_counter(); d.detect("I need to update the phone number linked to my account.", context={"original_text": "x"}); ts.append((time.perf_counter() - t0) * 1000)
    per[d.detector_id] = round(statistics.median(ts), 2)
lat["per_detector_ms_short"] = dict(sorted(per.items(), key=lambda kv: -kv[1])[:6])
json.dump(lat, open(os.path.join(HERE, "latency.json"), "w"), indent=1)
print(json.dumps(lat, indent=1))
