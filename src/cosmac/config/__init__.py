"""Configuration loader for cosmac (YAML + env vars + defaults)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from cosmac.exceptions import ConfigError

if TYPE_CHECKING:
    from cosmac.models import Severity

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "default.yaml"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides.

    Convention: COSMAC_<SECTION>_<KEY> in uppercase.
    """
    prefix = "COSMAC_"
    ps = config.get("cosmac", config)

    env_map: dict[str, tuple[str, ...]] = {
        f"{prefix}MODE": ("mode",),
        f"{prefix}THRESHOLD": ("threshold",),
        f"{prefix}DATA_DIR": ("data_dir",),
        f"{prefix}VAULT_ENABLED": ("vault", "enabled"),
        f"{prefix}VAULT_SIMILARITY_THRESHOLD": ("vault", "similarity_threshold"),
        f"{prefix}FEEDBACK_ENABLED": ("feedback", "enabled"),
        f"{prefix}CANARY_ENABLED": ("canary", "enabled"),
        # DEF-04: one name only. The inherited code mapped COSMAC_LOGGING_LEVEL
        # to a key nothing read, while api.py read COSMAC_LOG_LEVEL, so
        # neither variable did what its name suggested.
        f"{prefix}LOG_LEVEL": ("logging", "level"),
    }

    for env_key, path in env_map.items():
        value = os.environ.get(env_key)
        if value is None:
            continue

        if value.lower() in ("true", "false"):
            coerced: Any = value.lower() == "true"
        else:
            try:
                coerced = float(value)
            except ValueError:
                coerced = value

        target = ps
        for part in path[:-1]:
            target = target.setdefault(part, {})
        target[path[-1]] = coerced

    return config


def load_config(
    config_path: str | None = None,
    config_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load configuration from YAML file, dict override, and env vars.

    Priority (highest to lowest):
    1. Environment variables
    2. config_dict parameter
    3. config_path YAML file
    4. Default config
    """
    try:
        with open(_DEFAULT_CONFIG_PATH) as f:
            config = yaml.safe_load(f)
    except Exception as exc:
        raise ConfigError(f"Failed to load default config: {exc}") from exc

    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
        try:
            with open(path) as f:
                user_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, user_config)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if config_dict:
        if "cosmac" in config_dict:
            config = _deep_merge(config, config_dict)
        else:
            config = _deep_merge(config, {"cosmac": config_dict})

    config = _apply_env_overrides(config)

    return config


def resolve_data_dir(config: dict[str, Any]) -> Path:
    """Resolve the data directory path."""
    ps = config.get("cosmac", config)
    explicit = ps.get("data_dir")

    if explicit:
        return Path(explicit)

    if Path(".cosmac.yaml").exists():
        return Path(".cosmac")

    return Path.home() / ".cosmac"


def get_detector_config(config: dict[str, Any], detector_id: str) -> dict[str, Any]:
    """Get per-detector config, falling back to global defaults.

    Returns all detector-specific keys plus ``enabled`` and ``threshold``
    with sensible defaults so that custom detectors (e.g. d022) can
    receive extra settings like ``model_name`` or ``device``.
    """
    ps = config.get("cosmac", config)
    detectors = ps.get("detectors", {})
    detector_cfg = dict(detectors.get(detector_id, {}))

    detector_cfg.setdefault("enabled", True)
    detector_cfg.setdefault("severity", None)
    detector_cfg.setdefault("threshold", ps.get("threshold", 0.7))
    return detector_cfg


def get_action_for_severity(config: dict[str, Any], severity: Severity) -> str:
    """Get the configured action for a given severity level."""
    ps = config.get("cosmac", config)
    actions = ps.get("actions", {})
    return actions.get(severity.value, ps.get("mode", "block"))


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate configuration, returning a list of error messages (empty = valid)."""
    errors: list[str] = []
    ps = config.get("cosmac")
    if not ps:
        errors.append("Missing top-level 'cosmac' key")
        return errors

    mode = ps.get("mode", "block")
    if mode not in ("block", "monitor", "flag"):
        errors.append(f"Invalid mode: {mode}. Must be block, monitor, or flag")

    threshold = ps.get("threshold", 0.7)
    if not isinstance(threshold, (int, float)) or not 0.0 <= threshold <= 1.0:
        errors.append(f"Invalid threshold: {threshold}. Must be 0.0-1.0")

    vault = ps.get("vault", {})
    sim_thresh = vault.get("similarity_threshold", 0.85)
    if not isinstance(sim_thresh, (int, float)) or not 0.0 <= sim_thresh <= 1.0:
        errors.append(f"Invalid vault similarity_threshold: {sim_thresh}")

    errors.extend(_unknown_key_errors(ps))
    return errors


def _known_keys() -> dict[str, set[str]]:
    """Top-level sections and their keys, read from the shipped default.

    Using the shipped file as the authority means a key added to
    ``default.yaml`` is automatically accepted, while a key that exists only
    in a user's file is reported.
    """
    with _DEFAULT_CONFIG_PATH.open(encoding="utf-8") as fh:
        default = (yaml.safe_load(fh) or {}).get("cosmac", {})
    known: dict[str, set[str]] = {}
    for section, value in default.items():
        known[section] = set(value) if isinstance(value, dict) else set()
    return known


def _unknown_key_errors(ps: dict[str, Any]) -> list[str]:
    """Report keys that no code reads — DEF-04.

    The inherited configuration carried four keys nothing read
    (``history.store_input_text``, ``vault.max_entries`` and three
    ``threat_feed`` keys), so an operator could set them and silently get no
    behaviour. Unknown keys are now an error rather than a shrug.

    ``detectors`` is exempt: detector IDs are open-ended by design and
    third-party detectors register their own configuration.
    """
    known = _known_keys()
    errors: list[str] = []

    for section, value in ps.items():
        if section not in known:
            errors.append(
                f"Unknown configuration section '{section}'. Nothing reads it. "
                f"Known sections: {', '.join(sorted(known))}"
            )
            continue
        if section == "detectors" or not isinstance(value, dict):
            continue
        allowed = known[section]
        if not allowed:
            continue
        for key in value:
            if key not in allowed:
                errors.append(
                    f"Unknown key '{section}.{key}'. Nothing reads it. "
                    f"Known keys in '{section}': {', '.join(sorted(allowed))}"
                )
    return errors


def configure_logging(config: dict[str, Any] | None = None) -> str:
    """Apply ``cosmac.logging.level`` to the ``cosmac`` logger — DEF-04.

    The inherited configuration carried a ``logging`` block that no code
    read, so setting it had no effect. Returns the level that was applied.
    """
    import logging

    cfg = config if config is not None else load_config()
    section = cfg.get("cosmac", cfg)
    level_name = str(section.get("logging", {}).get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.getLogger("cosmac").setLevel(level)
    return level_name
