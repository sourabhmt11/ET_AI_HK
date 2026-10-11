# Licence register

**Story:** EVL-04 (M0) &middot; **Owner:** Product owner &middot; **Implements:** spec 7.4, 9.3, 10.3

Every model this code downloads, every dataset named in spec section 10.3, and
every extraction library named in spec section 7.4 is listed here.

> **Rule.** An entry marked **not confirmed** may not be relied upon by any
> story. Confirmation means a named person opened the source page on the date
> shown and recorded the licence there. Phase 0 was carried out without
> network access to those pages, so every row below that needs a human to read
> a licence page is marked *not confirmed* and carries the URL to check.

Legend for **Use**: **yes** = cleared for use &middot; **no** = must not be used
&middot; **pending** = blocked until confirmed.

---

## 1. Models downloaded at runtime

| Model | Used by | Licence (claimed) | Source | Checked | Use |
|---|---|---|---|---|---|
| `protectai/deberta-v3-base-prompt-injection-v2` | `d022` semantic classifier | Apache-2.0 (claimed on the model card; **not confirmed**) | https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2 | — | **pending** |
| `sentence-transformers/all-MiniLM-L6-v2` | Vault embedder (`vault/embedder.py`) | Apache-2.0 (claimed; **not confirmed**) | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | — | **pending** |
| `distilgpt2` | `d035` perplexity-spectral (opt-in) | Apache-2.0 (claimed; **not confirmed**) | https://huggingface.co/distilgpt2 | — | **pending** |

**Note on model IDs.** Spec section 9.1 keeps these identifiers unchanged
through the rename, until the classifier is replaced under FR-27. The phase 0
classifier benchmark (SPK-02) feeds decision 9.

**Revision pinning is not yet done.** All three download the current revision
on first use. Spec section 9.2 requires pinned revisions; that is tracked
separately and is not closed by this register.

---

## 2. Datasets (spec section 10.3)

| Dataset | Purpose | Licence | Source | Checked | Use |
|---|---|---|---|---|---|
| deepset prompt-injections | Direct injection | **not confirmed** | https://huggingface.co/datasets/deepset/prompt-injections | — | **pending** |
| Liu et al. Open-Prompt-Injection | Direct injection | **not confirmed** | https://github.com/liu00222/Open-Prompt-Injection | — | **pending** |
| InjecAgent | Indirect / agentic | **not confirmed** | https://github.com/uiuc-kang-lab/InjecAgent | — | **pending** |
| AgentDojo | End-to-end attack success + utility | **not confirmed** | https://github.com/ethz-spylab/agentdojo | — | **pending** |
| BIPIA | Indirect | **not confirmed** | https://github.com/microsoft/BIPIA | — | **pending** |
| LLMail-Inject | Indirect | **not confirmed** | — | — | **pending** |
| NotInject (339 samples) | Hard benign | **not confirmed** | https://huggingface.co/datasets/leolee99/NotInject | — | **pending** |
| PINT | External reference only | Partly proprietary, scored by its maintainer | https://github.com/lakeraai/pint-benchmark | 2026-10-11 | **no** — cannot be self-run; reference only |
| JailbreakBench | Red-team harness only | **not confirmed** | https://github.com/JailbreakBench/jailbreakbench | — | **pending** |
| HarmBench | Red-team harness only | **not confirmed** | https://github.com/centerforaisafety/HarmBench | — | **pending** |
| Garak | Scanner, not a gate | **not confirmed** | https://github.com/NVIDIA/garak | — | **pending** |
| COSMAC in-domain benign corpus | Hard benign | Customer-supplied; terms set by decision 12 | — | — | **pending** — blocked on decision 12 |
| COSMAC multi-turn set | Multi-turn | Does not exist yet | — | — | n/a |
| COSMAC hidden-content corpus | Documents and images | Does not exist yet | — | — | n/a |

---

## 3. Extraction libraries (spec section 7.4)

| Library | Purpose | Licence | Checked | Use |
|---|---|---|---|---|
| **PyMuPDF** | PDF extraction | AGPL-3.0 / commercial | 2026-10-11 | **no** — recorded in spec 10.3 and backlog EVL-04 as not permitted |
| pdfminer.six | PDF text layer | MIT (**not confirmed**) | — | **pending** — candidate for ING-07 |
| pypdf | PDF text layer | BSD-3-Clause (**not confirmed**) | — | **pending** — candidate for ING-07 |
| python-docx | Word extraction | MIT (**not confirmed**) | — | **pending** |
| Tesseract / pytesseract | OCR | Apache-2.0 / MIT (**not confirmed**) | — | **pending** |

> **ING-07 is blocked** until one PDF library here is confirmed. PyMuPDF is
> recorded as **not permitted** and must not be reintroduced.

---

## 4. Runtime dependencies

Direct dependencies are pinned with hashes in `requirements.lock`. Their
licences are the usual permissive set (MIT / BSD / Apache-2.0) as declared in
each package's metadata; a full machine-readable inventory is produced by the
SBOM work in NFR-13 (phase 3) and is **not** claimed as confirmed here.

Two dependencies are called out because spec section 9.4 raised them:

| Dependency | Note |
|---|---|
| `cryptography>=50.0.0,<51` | Floor set upstream to exclude CVE-2026-69247/-69248/-69249 |
| `mcp>=1.10,<2` | Upper bound added by REP-03; the code targets the 1.x API |

---

## 5. What this register does not cover

- Per-file copyright headers. The upstream codebase ships none; COSMAC adds
  none. Attribution is in `NOTICE`.
- Trademark. Apache-2.0 grants no trademark rights; see `NOTICE`.
- The upstream logo and architecture image, which were **removed** rather than
  rebranded (REP-02).
