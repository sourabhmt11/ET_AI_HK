# MCP registry submissions — paste-ready

Registries where the `cosmac` MCP server belongs. Each entry below is
formatted for the registry's expected shape and can be pasted into a PR or a
form. **None of these are auto-submitted** — submit them yourself, in your
own name, when you're ready.

Update the version number and any counts to match the shipped release before
submitting.

---

## 1. `modelcontextprotocol/servers` — official community list

**Repo:** https://github.com/modelcontextprotocol/servers
**How:** Open a PR adding an entry to the community-servers table in the
README.
**Category:** Security / guardrails.

Paste as a new row in the community table:

```markdown
- **[prompt-shield](https://github.com/mthamil107/prompt-shield)** — Prompt-injection firewall for LLM applications. Exposes `scan_input`, `scan_output`, `scan_tool_result`, and `list_detectors` tools backed by 34+ input detectors, a federated ed25519-signed threat feed, and a tool-result boundary primitive.
```

---

## 2. `punkpeye/awesome-mcp-servers`

**Repo:** https://github.com/punkpeye/awesome-mcp-servers
**How:** Open a PR adding an entry alphabetically under **Security** (create
the section if it doesn't exist).

```markdown
- [prompt-shield](https://github.com/mthamil107/prompt-shield) 🐍 🏠 - Prompt-injection firewall. Scans user input, LLM output, and tool-result content for injection, jailbreaks, PII, code injection, and toxicity via 34+ detectors with a federated ed25519-signed threat feed.
```

Legend used by that repo: 🐍 = Python, 🏠 = self-hosted, ☁️ = cloud, 🍎 =
macOS, 🐧 = Linux, 🪟 = Windows.

---

## 3. `wong2/awesome-mcp-servers`

**Repo:** https://github.com/wong2/awesome-mcp-servers
**How:** PR adding to `Community Servers` or a `Security` subsection.

Same content as entry #2 above works here.

---

## 4. `appcypher/awesome-mcp-servers`

**Repo:** https://github.com/appcypher/awesome-mcp-servers
**How:** PR adding to a Security or Guardrails section.

Same content as entry #2 above.

---

## 5. Smithery.ai — hosted MCP registry

**Site:** https://smithery.ai/
**How:** Sign in with GitHub, click "Add server", fill in the form. Smithery
scrapes your repo's `smithery.yaml` if present.

Suggested form values:

* **Server ID:** `mthamil107/cosmac`
* **Command:** `cosmac-mcp`
* **Description:**
  Prompt-injection firewall exposing scan_input, scan_output,
  scan_tool_result, and list_detectors tools. Backed by 34+ detectors and a
  federated signed threat-intel feed.
* **Category:** Security
* **License:** Apache 2.0

Optionally check in a `smithery.yaml` at the repo root:

```yaml
name: cosmac
description: Prompt-injection firewall for LLM applications
version: 0.8.0
runtime: python
command: cosmac-mcp
args: []
env:
  COSMAC_CONFIG:
    description: Optional path to a custom cosmac YAML config
    required: false
```

---

## 6. MCP.so registry

**Site:** https://mcp.so/
**How:** Submit via the "Submit Server" form on the site.

Same values as Smithery.

---

## 7. PulseMCP registry

**Site:** https://www.pulsemcp.com/
**How:** They index public MCP servers automatically once you're in one of
the awesome-lists above. No direct submission needed.

---

## Suggested submission order

The goal is durable presence with minimum friction. Prioritise registries
that require no ongoing maintenance:

1. **`modelcontextprotocol/servers`** — official, most authoritative, highest
   discovery signal. Do this first.
2. **`punkpeye/awesome-mcp-servers`** — largest community list on GitHub.
3. **Smithery.ai and MCP.so** — hosted registries with search + install UIs.
   Higher upside because a Cursor user can install by clicking, not by
   editing JSON.
4. The remaining awesome-lists — small individual upside; do them once and
   forget.

## Timing note

Submit only after you have:

* Cut a `v0.8.0` release tag on GitHub with the MCP server changelog entry
  visible.
* Published `cosmac==0.8.0` to PyPI so `pip install
  "cosmac[mcp]"` picks up the console script.
* Manually tested `cosmac-mcp` end-to-end in Claude Desktop or Cursor
  so the demo transcript in `docs/mcp-server.md` is reproducible.

Submitting before those three steps produces broken listings that maintainers
close.

## After the PRs merge

Add merged registry URLs to `docs/mcp-server.md` under a "Where to find
cosmac" section — that's evergreen social proof for anyone reading
the docs later.
