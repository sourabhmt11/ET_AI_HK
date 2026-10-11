# COSMAC specification: independent review

**Reviewed document:** COSMAC_SPEC.md, draft v1.0
**Review date:** 2026-10-10 to 2026-10-11
**Outcome:** v1.0 was not accepted. All three reviewers found blockers. The spec was revised to v1.1; section 5 of this document records what changed and what remains open.

---

## 1. How the review was run

Three reviewers worked independently of the team that wrote the spec and of each other. Each received the customer requirement, the spec, the codebase and the raw evidence files. None received the build team's working reports.

| Reviewer | Question asked | Method |
|---|---|---|
| Product reviewer | Does the spec meet the customer requirement? | Traced every input source, attack type, depth level and key phrase to the spec; checked the acceptance criteria and their arithmetic; recounted figures from the evidence files |
| Security reviewer | Would this stand up as a security control by current industry standards? | Fact-checked standards and competitor claims against primary sources; attacked the proposed design; gave a buyer's verdict for three deployment types |
| Principal engineer | Is the spec true and buildable? | Opened the cited code for 46 claims; re-ran the measurements; read the probe set for labelling problems; assessed feasibility, sizing and the rename plan |

---

## 2. Verdicts

### 2.1 Product as specified in v1.0, against the requirement

| Level | Verdict | Main reason |
|---|---|---|
| D1 | Meets with conditions | Architecture is right, but the D1 thresholds were not testable and two gaps rated Critical were scheduled for D2 |
| D2 | Does not meet as written | "Demonstrable reliability" could not be demonstrated with the stated sample sizes; PDF and Word were excluded without the customer's agreement |
| D3 | Does not meet as written | 20 samples per matrix cell cannot support per-source reliability claims; latency targets conflict with full-document scanning |

### 2.2 Current codebase, against the requirement

| Level | Verdict |
|---|---|
| D1 | Does not meet |
| D2 | Does not meet |
| D3 | No capability: binary input raises an error, and there is no parser or OCR |

### 2.3 Buyer's security verdict on the v1.0 design

| Deployment | Verdict | Conditions |
|---|---|---|
| Chatbot with no tools | Approve with conditions | D2 delivered and measured; authentication from the first gateway release; learning loops off; output egress control |
| RAG assistant over internal documents | Approve with conditions | As above, plus the security blockers closed, D3 evidence for the formats actually ingested, and a written threat model |
| Autonomous agent with write tools and web access | Reject as the sole control | Acceptable only as one layer beside controls that do not depend on it: least-privilege tool credentials, deterministic tool policy, egress allowlist, approval |

### 2.4 Technical accuracy of v1.0

| Check | Result |
|---|---|
| Code claims checked | 46: 40 confirmed, 0 wrong, 5 partly right, 1 citation off |
| All claims rated Critical | Confirmed |
| Measured figures | All reproduced exactly on an independent re-run (see section 4) |
| Buildable as written | No: D1 exit criteria depended on phase 2 work, latency targets were 2 to 6 times beyond current CPU performance, and several requirements were untestable as worded |

---

## 3. Findings

Severity: **Blocker** means the spec cannot be accepted until fixed. **Major** materially weakens it. **Minor** is a correction.

### 3.1 Blockers

| # | Finding | Raised by | Disposition in v1.1 |
|---|---|---|---|
| B1 | **Sample sizes cannot demonstrate the thresholds.** 180/200 demonstrates recall above about 85%, not 90%, and the result depends on an interval method the spec did not name. No benign sample size was stated; showing a 1% false-positive ceiling needs roughly 1,200 samples. Twenty payloads per matrix cell can never show an 85% lower bound, and re-rendering 20 payloads into 11 sources does not give independent samples. | Product, Security, Engineer | Fixed. Section 10 names the interval method, states attack and benign sample sizes per gate, requires independent payloads, and gates D3 per source and per type with cells reported only. |
| B2 | **PDF and Word were deferred to D3 by interpretation.** The requirement says D1 and D2 are "mostly" textual. Text-layer PDFs and Word files are textual. Behaviour when a PDF arrived at D1 was undefined. | Product | Fixed. Text-layer extraction for PDF and Word moves to D1; hidden-content analysis stays at D3. Recorded as an open decision for the customer. |
| B3 | **Gaps rated Critical were closed too late.** No authentication and fail-open were scheduled for phase 2, so the D1 gateway would ship unauthenticated and failing open. Shared state was scheduled for D3 although sessions and multiple workers arrive earlier. | Product, Security, Engineer | Fixed. API-key authentication, fail-closed behaviour and readiness move to D1. The shared store moves to D2. |
| B4 | **D1 criteria were not verifiable, and the plan did not reach them.** The recall target was below today's figure, the benign test set did not exist, and the only mechanisms that reduce false positives were scheduled for D2. | Product, Engineer | Fixed. The classifier benchmark and a first calibrated decision stage move to phase 1. D1 gates are restated with sample sizes. Multi-step is measured with history supplied at D1 and stated as such. |
| B5 | **No threat model.** No attacker goals, capabilities or trust boundaries. Trust had two tiers, and the source type was declared by the caller, so content could be mislabelled to receive weaker checks. | Security, Product | Fixed. New section 3 adds a threat model, six trust tiers assigned by channel, and format sniffing. |
| B6 | **Exfiltration path barely specified.** Nothing covered markdown image or link URLs, URL arguments in tool calls, or scanning of streamed output. | Security | Fixed. New egress requirements at D1. |
| B7 | **"Intercepts all incoming content" was over-claimed.** The gateway cannot see provider-side tools, remote references, tools outside MCP, or content the model decodes or fetches after inspection. | Security, Product | Fixed. Section 3.4 lists what is and is not intercepted; remote references are blocked or must be inlined. |
| B8 | **Learning loops left on.** Automatic vault storage, feedback-driven threshold tuning and the remote feed are on by default and can be poisoned: an attacker can make the vault block legitimate business content, and false-positive feedback lowers detection for everyone. | Security | Fixed. All three are off by default from D1; when enabled they are offline, reviewed and per tenant. |
| B9 | **Latency targets conflict with full-document scanning.** Measured in-process medians are 288 ms at 2,000 characters and 455 ms at 3,200. Full classifier coverage of 32,000 characters is about 83 windows, or 1.6 to 3.4 seconds before other detectors. | Engineer, Product | Fixed. Targets are now provisional and set after a performance spike in phase 0; the levers are listed. |

### 3.2 Major findings

| # | Finding | Raised by | Disposition in v1.1 |
|---|---|---|---|
| M1 | Metrics undefined for the new action model: whether a sanitised or flagged-and-forwarded attack counts as caught; "content preserved" had no unit. | Product | Fixed: success is defined as the injected instruction not reaching the model in actionable form. |
| M2 | Gaps with no closing requirement: the allowlist bypass, middleware pass-through on parse failure, API cannot load a config file, LangChain sanitise does nothing. | Product, Security | Fixed: requirements added. |
| M3 | Requirements with no delivery phase (SDK wrapper rework, structural anomaly signals, hardening, CI audit gates, refactor backlog). A dependency inversion: the D1 policy consumed a decision band produced at D2. | Product, Engineer | Fixed in the delivery plan. |
| M4 | Attack types with no requirement behind their stated weakness: context poisoning (D3 only), secret extraction, paraphrase. | Product | Partly fixed: a false-prior-agreement detector moves to D1. Paraphrase still depends on the classifier work and remains a stated risk. |
| M5 | The neutraliser is an attack surface: forgeable isolation markers and placeholders; an attacker can delete a chosen sentence by planting trigger phrasing in it; the removal report is a detection oracle. | Security | Fixed: per-request random markers, escaping of look-alikes, visible gap markers, quarantine as the default for contracts and code, detailed reports to administrators only. |
| M6 | Split and differential attacks not addressed: payloads split across segments, fields, documents or turns; differences between COSMAC's parser and the provider's; hidden channels missing from the lists. | Security | Fixed: cross-segment scan, forwarding of the canonical extracted form, extended channel lists, differential tests. |
| M7 | Second stage and uncertain band: the judge reads attacker text with no hardening; "uncertain, forwarded with a flag" is a pass. | Security | Fixed: judge has no tools and structured output, errors block; uncertain plus a sensitive capability blocks. |
| M8 | Denial of service: fail-closed on documents plus OCR and recursion with no limits lets one crafted document halt an agent; where chat fails open, forcing a timeout is a bypass. | Security, Engineer | Fixed: hard limits; no fail-open on deadline; process-based timeouts. |
| M9 | "Never leaves a partial payload" is unverifiable; the normaliser returns no offset map; decoded text has no raw offsets. | Engineer | Fixed: reworded as measured removal on a labelled corpus, with quarantine when span confidence is low. |
| M10 | Effort under-sized: canonicaliser, neutraliser with policy engine, MCP proxy and D1 adapters. | Engineer | Fixed: re-sized to L. |
| M11 | Streaming had no delivery row although most clients stream by default; every request resends full history with no verdict cache. | Engineer | Fixed: streaming pass-through at D1; content-hash verdict cache. |
| M12 | Calibrated decision stage has no data: source, channel and hidden-flag features exist in no public dataset; no independent test-set author role existed. | Engineer | Fixed: data plan and an independent evaluation author role added. Remains the largest delivery risk. |
| M13 | The only block-capable model comes from an archived project whose models are stated to be unmaintained. | Security | Fixed: replacement or an owned fine-tune is mandatory, with pinned hashes and a model inventory. |
| M14 | Blast-radius controls late and coarse: "untrusted content in context" is true on almost every agent turn; memory poisoning waits for D3; inter-agent messages absent; MCP proxy lacks the confused-deputy requirements the MCP guidance mandates. | Security | Partly fixed: capability classes per tool and MCP proxy requirements added at D2. Full information-flow tracking remains beyond D3. |
| M15 | Rename plan: mechanical and behavioural steps cannot be separated by find-and-replace; excluding test fixtures breaks imports; a blanket replace creates dead URLs; several identity surfaces missed; doctest CI runs the README. | Engineer | Fixed in section 9. |
| M16 | Missing sections: data handling, behaviour seen by the end user, API contract, rollout, assumptions. | Product | Fixed: added. |
| M17 | Evaluation datasets mis-described: the PINT set cannot be self-run; JailbreakBench and HarmBench measure model harm; Garak is a scanner; the adaptive round had no protocol. | Security | Fixed in section 10. |

### 3.3 Corrections to facts in v1.0

| v1.0 said | Correct | Source |
|---|---|---|
| LlamaFirewall is not under an OSI licence | The code is MIT; only its models are under Meta's Llama licences | Security reviewer, repository LICENSE |
| Compliance mappings can be reused as is | The MITRE ATLAS mapping has wrong names for three technique IDs and lacks four techniques the spec quotes | Security reviewer |
| MCP specification guidance supports tool-description scanning and pin-and-hash | That comes from OWASP's MCP Top 10 only | Security reviewer |
| The PINT harness is a usable dataset | Only the harness and an example file are public | Security reviewer |
| AgentDojo state of the art is attack success under about 2% with 5 points or less of utility loss | Could not be verified; removed | Security reviewer |
| Whole-document replacement was cited to the ML classifier | It comes from the homoglyph detector. Also, any benign document over 10,000 characters is replaced entirely in sanitise mode, because the long-input detector reports the whole document as its span | Engineer |
| Helm runs 2 replicas against one ReadWriteOnce volume | Persistence is off by default, so each pod has private ephemeral state; the conflict arises only if persistence is enabled | Engineer |
| No body-size limit | The `text` field is capped at 100,000 characters; `context` and the HTTP body are unbounded | Engineer |
| Source is never read | True at defaults; the opt-in fatigue tracker reads it | Engineer |
| Probe ran on the default engine with the vault off | History and feedback were also off | Engineer |
| Multi-step without the classifier: n/a | 1/12 | Product, Engineer |
| Regex detectors alone block 12/120 | That figure includes the alignment detector, which is not regex | Product |
| The classifier's false positives are flat across input length | The 1 to 2 word bucket is lower (2/24) than longer inputs (20 to 29%) | Product |
| A paraphrased attack was "missed" beyond 2,500 characters | Missed by the classifier; those inputs were still flagged by the blanket long-input detector | Product |
| Today's p95 of 115 ms shown beside a 2,000-character target | 115 ms is for inputs under 120 characters; at 2,000 characters the in-process median is 288 ms | Engineer |
| 427 import statements | About 450 | Engineer |
| "Core stays small" | Base dependencies already pull in torch | Engineer |
| All extraction libraries are permissive | `trafilatura` is Apache-2.0 only from version 1.8; `opencv-python` wheels bundle LGPL components | Engineer (from memory, to be confirmed) |

### 3.4 What the reviewers found sound

- The current-state audit is candid, and the spec declines to claim prevention.
- Every headline figure matched the stored evidence and reproduced on an independent run.
- Limits of the evidence were disclosed: single author, hard-benign design, small cells, no real PDF or OCR extraction.
- Segment-based ingestion with hidden-channel labels, trust-tiered policy and a gateway is the right architecture, and the prototype evidence supports it.
- The neutraliser requirements address defects that reproduce.
- The sealed test set, separate authorship and separate adaptive reporting are right in principle.
- The "keep unchanged" list in the rename plan is safe, and no compatibility shim is needed for the repository itself.

---

## 4. Independent reproduction

Run by the principal engineer in a scratch directory, vault off, data directory redirected.

| Figure | Spec | Re-run | Match |
|---|---|---|---|
| Attacks blocked | 93/120 | 93/120, no action differs across 240 samples | Yes |
| Benign blocked | 31/120 | 31/120 | Yes |
| Per-type table, style table, classifier-only counts | As stated | Identical | Yes |
| Ablation rows | As stated | Identical | Yes |
| Input sources, raw | 38/39 and 24/31 | 38/39 and 24/31 | Yes |
| Input sources, segmented | 16/31; 14/31 with 36/39; 15/17 hidden | Identical | Yes |
| Sanitiser garbling | Yes | Reproduced | Yes |
| Long-input blind spot (reviewer's own document and paraphrase) | First 3,200 characters or so | Blocked at 365 and 2,801; passed at 3,298, 5,929 and 8,891 | Yes |
| Long-input flag | Every input over 10,000 characters | 10,200 flagged; 9,800 passed | Yes |
| Model load failure | Fails open | Attack passed with no error | Yes |
| Same text as user input and as tool result | Identical decision | Identical | Yes |
| MCP tests | 13 fail | 13 failed, 5 passed | Yes |
| In-process latency | p50 47 ms, p95 68 ms short; 1.09 s at 10,000 characters | 42 ms, 56 ms; 0.93 s | Yes |

### Probe-set quality

The engineer read the probe set and found labelling and diversity problems that widen the uncertainty on the headline figures without changing the conclusions.

| Problem | Effect |
|---|---|
| Tool-abuse items written as direct user messages are legitimate requests from an authorised user; the probe has no source field | The 7/13 tool-abuse figure is not a clean recall figure |
| Multi-step items are context-free last turns, mostly harmful-content requests and not injection | The 5/12 figure mixes two problems, one of which is out of scope |
| The embedded attacks (13 in the stored results) share one carrier document with the payload at the same position | The embedded result is on easy material |
| 8 of 16 encoded items encode the same sentence | The encoded result is on easy material |
| Two benign items are model-directed instructions; two are truncated fragments | Slight overstatement of the benign block rate |
| 12 to 16 samples per type | 7/13 has a 95% interval of roughly 29% to 77% |

Estimated effect: attack recall could be anywhere from about 75% to 86% after relabelling, and the benign block rate 25% to 30%. The findings that the product depends on one classifier and over-blocks hold either way.

---

## 5. Status after revision to v1.1

| Item | Status |
|---|---|
| Blockers B1 to B9 | Addressed in the text of v1.1. A re-review found six closed and three partly closed; see section 6. |
| Major findings | Addressed, except M4 and M14, which are partly addressed and recorded as risks |
| Fact corrections | All applied |
| Not verified by any reviewer | The server latency and throughput figures (76 ms, 115 ms, 12 requests per second); the claim that tests write to the home directory; the standards rows for NIST, the EU AI Act, ISO and SOC 2 against primary texts; several competitor rows (Microsoft, Kong, Cloudflare, NeMo, Guardrails AI, LiteLLM); licences of the models and of some extraction libraries |

### Open risks the review could not close

1. **The reliability targets are a research risk, not a plan.** The classifier COSMAC inherits scores 79.1% on the PINT benchmark as published by its maintainer. D2 asks for 90% per attack type with a 1% benign ceiling. Whether a replacement classifier and a calibrated decision stage reach that is unknown until measured.
2. **Latency.** No design in v1.0 supported the targets. v1.1 makes them provisional pending a spike.
3. **Autonomous agents.** The security reviewer would not approve COSMAC as the sole control for an agent with write-capable tools at any depth level. This is a limit of the product category, and v1.1 states it.
4. **Evaluation data.** The sealed test sets, the in-domain benign corpus and the document corpus do not exist. Building them is a large part of the work and needs authors independent of the detector team.

### Recommended next step

Have the revised spec (v1.1) re-reviewed against findings B1 to B9 before committing to the delivery plan, and run the phase 0 performance spike and classifier benchmark first, since both can invalidate the D2 targets.

---

## 6. Re-review of v1.1: readiness for development

**Date:** 2026-10-11
**Reviewer:** an independent engineering lead who had seen neither draft
**Verdict: ready to start phase 0 only.**

v1.1 closes most of the v1.0 findings, and phase 0 plus a few phase 1 fixes need no further decisions. Phase 1 as a whole is not ready: the interfaces it is built on are described and not specified, several D1 requirements depend on D2 work, and D1 has no time box or team size.

### 6.1 Closure of the v1.0 findings

| Result | Count | Items |
|---|---|---|
| Closed | 15 of 26 | B1, B2, B5, B7, B8, B9, M2, M6, M7, M8, M9, M10, M13, M15, M17 |
| Partly closed | 11 of 26 | B3, B4, B6, M1, M3, M4, M5, M11, M12, M14, M16 |
| Fact corrections | 18 of 18 applied | |

| Partly closed | What remains |
|---|---|
| B3 | Multiple workers arrive at D1 but shared state at D2, and `session_id` is already in the D1 API |
| B4 | The D1 per-type gate covers multi-step attacks, whose detector fixes are in phase 2 |
| B6, M11 | D1 streaming is pass-through, so a streamed reply can bypass egress control; tool-call argument assembly is D2 |
| M1 | "Content preserved" is measured against COSMAC's own extraction; "no garbled output" and "actionable form" have no test |
| M3 | No phase 1 row for model pinning; NFR-14 unscheduled; the feedback endpoint has no requirement |
| M5 | The API sketch still returns the location and reason of each removal to the caller, which is the detection oracle the finding warned about |
| M12 | No owner, size or source for training and calibration data |
| M4, M14, M16 | As recorded in section 3.2 |

### 6.2 New problems in v1.1

| # | Severity | Problem |
|---|---|---|
| N1 | Blocker | **The forwarded "canonical form" is undefined.** Nothing says what it is for JSON or XML tool results an agent must parse, for source code, or for HTML links. Section 8.1 says ALLOW passes content unchanged while FR-31 says retrieved content is always wrapped. |
| N2 | Blocker | **Core interfaces are not specified.** The segment and document model is a field list with no types. The policy file has no schema. The API sketch has no error codes, no file-upload encoding, and no rule for where isolation markers go in a proxied chat request. |
| N3 | Major | Trust tiers do not map cleanly onto a provider-format request: system messages arrive in the request body, and a file attached to a user turn has no tier. |
| N4 | Major | D1 requirements depend on D2 work: administrator-only removal detail needs the D2 audit; per-tenant allowlists need D2 tenancy; the "sensitive capability" rule needs D2 capability classes. |
| N5 | Major | Fetching remote references (FR-6) has no SSRF rules and conflicts with default-deny egress. |
| N6 | Major | CPU-time limits need killable worker processes, which arrive at D3, while PDF and Word parsing starts at D1. |
| N7 | Major | Two D1 gates conflict unless the denominator is defined: a 5% benign block rate and 98% content preserved on benign documents. |
| N8 | Major | **D1 is large.** Phase 0 is about 6 to 12 pair-weeks and phase 1 about 23 to 46, so D1 is roughly 4 to 6 months elapsed even with parallel tracks. One evaluation author is to write 1,450 independent samples in the same phase. |
| N9 | Minor | Arithmetic and counts: fixed in the spec on 2026-10-11 (sample size for a 90% lower bound, the D1 per-type gate, the embedded-attack count, the matrix size). |
| N10 | Minor | Untestable wording remains in FR-11, FR-25, FR-32 and FR-33. Per-request random markers defeat provider prompt caching. |

N1 to N8 are open. Only N9 has been corrected.

### 6.3 Work that can start now

- Repository baseline: fork remote, tag, NOTICE, lockfile, the `mcp` pin, and committing the spec and evidence.
- Phase 0 items of the defects register.
- Learning loops off by default, the allowlist fix, and rejection on parse failure.
- The evaluation command and the two spikes.
- Decision-free phase 1 fixes: decoder wiring, the noisy-detector fixes, bidirectional controls, fail-closed, worker pool, readiness, hardening, API keys.
- The rename, once a code freeze and the distribution name are agreed. It touches about 350 files in one commit, so nothing else should run in parallel with it.

### 6.4 Decisions needed from the product owner

| Decision | Blocks | Default if undecided |
|---|---|---|
| Hackathon demo or product build; team size and time box | Everything after phase 0 | The plan is unbounded |
| First provider format | Gateway | OpenAI chat completions |
| First deployment shape | Gateway and SDK priority | Single gateway |
| Canonical form for structured content; whether originals may be forwarded | Adapters, neutraliser, inspect API | None; this is N1 |
| PDF and Word at D1 | Phase 1 size | D1 as written |
| Acceptance thresholds | D1 exit | No exit criteria |
| In-domain benign data: who supplies it, on what terms | D1 benign gate, calibration | The gate cannot be run |
| Who is the evaluation author | Test sets | Independence is lost |
| Reference hardware | Latency targets | Whatever the spike machine was |
| Repository, package and registry ownership | Rename, Helm and Action defaults | Rename locally, do not publish |
| Fail mode for user chat; tenancy at D1 | Failure handling, egress allowlists | Fail closed; one tenant per key |

### 6.5 Blocked on measurement, not on a person

- Performance spike: sets latency targets and whether full cross-segment scanning is affordable.
- Classifier benchmark: decides retrain or replace, and whether the D2 targets are feasible.
- First reliability report: feeds the thresholds.
- Feasibility of the offset map through decoding.
- Whether isolation markers work per model family, and how much task utility is lost by forwarding canonical text. The spec does not yet plan these two spikes.

### 6.6 Missing for a development start

A story-level backlog, a definition of done per phase, schemas (segments, policy file, audit record, errors, an OpenAPI document), a demo scenario with a reference agent, a test strategy and phase 1 CI gate, a plan for development and validation data, environment setup, and a branching and freeze rule around the rename.
