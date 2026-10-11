# Pre-commit Hook Integration

COSMAC provides pre-commit hooks that scan staged files for prompt
injection patterns and PII before every commit. This catches security issues
early, before they enter your repository.

## Available Hooks

| Hook ID | Description |
|---------|-------------|
| `cosmac-scan` | Scans for prompt injection patterns (role hijacking, instruction override, etc.) |
| `cosmac-pii` | Scans for PII (emails, phone numbers, SSNs, credit card numbers, etc.) |

## Setup

### 1. Install pre-commit

```bash
pip install pre-commit
```

### 2. Add to your `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/mthamil107/prompt-shield
    rev: v0.3.0
    hooks:
      - id: cosmac-scan
      - id: cosmac-pii
```

### 3. Install the hooks

```bash
pre-commit install
```

Now COSMAC will automatically scan every staged text file when you run
`git commit`.

## Configuration

### Threshold

Adjust the confidence threshold for prompt injection detection (default: 0.7).
Lower values are more sensitive; higher values reduce false positives.

```yaml
repos:
  - repo: https://github.com/mthamil107/prompt-shield
    rev: v0.3.0
    hooks:
      - id: cosmac-scan
        args: ["--threshold", "0.8"]
```

### Excluding Files

Skip files that match glob patterns:

```yaml
repos:
  - repo: https://github.com/mthamil107/prompt-shield
    rev: v0.3.0
    hooks:
      - id: cosmac-scan
        args: ["--exclude", "*.min.js", "--exclude", "vendor/*"]
      - id: cosmac-pii
        args: ["--exclude", "tests/fixtures/*"]
```

You can also use the built-in `exclude` key from pre-commit:

```yaml
hooks:
  - id: cosmac-scan
    exclude: "^(vendor/|node_modules/)"
```

### Using Only One Hook

You do not need to enable both hooks. Pick the ones relevant to your project:

```yaml
# Only scan for prompt injection
hooks:
  - id: cosmac-scan
```

```yaml
# Only scan for PII
hooks:
  - id: cosmac-pii
```

## How It Works

### Prompt Injection Hook

The `cosmac-scan` hook runs each staged text file through the
CosmacEngine with a lightweight configuration optimized for speed:

- Vault, feedback, canary, and history subsystems are disabled
- The semantic classifier (which requires ML model downloads) is disabled
- Only fast regex-based and heuristic detectors run

Files that trigger any detector above the confidence threshold cause the commit
to be blocked.

### PII Hook

The `cosmac-pii` hook uses the PIIRedactor to scan for common PII
patterns including:

- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- AWS keys and other API credentials

Any PII detection blocks the commit.

## Output

Clean files show green PASS output:

```
PASS src/app.py
PASS config/settings.yaml
```

Detections show red FAIL output with details:

```
FAIL prompts/system.txt — 2 detection(s), risk score 0.85
  [HIGH] d001_instruction_override (confidence: 0.82)
    Detected instruction override pattern
    Line 5: 'ignore all previous instructions'
```

## Running Manually

Run the hooks against all files without committing:

```bash
pre-commit run cosmac-scan --all-files
pre-commit run cosmac-pii --all-files
```

Run against specific files:

```bash
pre-commit run cosmac-scan --files src/prompts/*.txt
```

## CI Integration

Add to your CI pipeline to scan all files on every push:

```yaml
# GitHub Actions example
- name: Run COSMAC hooks
  run: |
    pip install pre-commit
    pre-commit run cosmac-scan --all-files
    pre-commit run cosmac-pii --all-files
```
