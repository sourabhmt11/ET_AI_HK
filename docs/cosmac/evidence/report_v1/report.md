# COSMAC reliability report

## Provenance

| Field | Value |
|---|---|
| Generated (UTC) | 2026-10-11T10:38:27+00:00 |
| Commit | `43c8d30420dbc2218f10836311b006f6dbc9dc92` |
| Configuration hash | `7fc9c1747d2f723d…` |
| Sample set | `docs/cosmac/evidence/probe_set_v1.jsonl` |
| Sample-set SHA-256 | `f8e7210c374f7040…` |
| Samples | 240 |
| Machine | Windows 11 / AMD64 / Python 3.12.2 |
| Classifier | `protectai/deberta-v3-base-prompt-injection-v2` |
| Embedding model | `all-MiniLM-L6-v2` |
| Classifier loaded | True |

## Headline figures

Every rate is given as observed value, 95% Wilson interval, and denominator. No figure in this report may be quoted without its interval.

| Measure | Value |
|---|---|
| Attack detection, overall | 80.0% [72.0-86.2%] n=120 |
| Benign block rate | 27.5% [20.3-36.1%] n=120 |

## By attack type

| Attack type | Detection rate |
|---|---|
| `context_poisoning` | 92.3% [66.7-98.6%] n=13 |
| `credential_theft` | 61.5% [35.5-82.3%] n=13 |
| `encoded_instruction` | 93.8% [71.7-98.9%] n=16 |
| `indirect_injection` | 71.4% [45.4-88.3%] n=14 |
| `instruction_override` | 100.0% [77.2-100.0%] n=13 |
| `multi_step` | 58.3% [32.0-80.7%] n=12 |
| `role_change` | 92.3% [66.7-98.6%] n=13 |
| `secret_extraction` | 92.3% [66.7-98.6%] n=13 |
| `tool_abuse` | 53.8% [29.1-76.8%] n=13 |

## By source type

| Source | Detection rate |
|---|---|
| `docx` | 0.0% [0.0-79.3%] n=1 |
| `email` | 50.0% [9.5-90.5%] n=2 |
| `html` | 75.0% [30.1-95.4%] n=4 |
| `json` | 100.0% [20.7-100.0%] n=1 |
| `markdown` | 100.0% [20.7-100.0%] n=1 |
| `ocr_text` | 100.0% [20.7-100.0%] n=1 |
| `pdf` | 0.0% [0.0-79.3%] n=1 |
| `plain_text` | 100.0% [34.2-100.0%] n=2 |
| `source_code` | 100.0% [20.7-100.0%] n=1 |
| `user_message` | 81.1% [72.6-87.4%] n=106 |

## In-process latency

Measured on: Windows 11 / AMD64 / Python 3.12.2

| Length bucket | n | p50 (ms) | p95 (ms) |
|---|---|---|---|
| 0-500 | 218 | 122.02 | 164.09 |
| 501-2k | 22 | 523.73 | 563.5 |

## Independence (spec 10.1)

- Samples: 240
- Independent payloads: 240
- Independent carriers: 240
- Payload IDs reused across samples: 0
- Carrier IDs reused across samples: 0

