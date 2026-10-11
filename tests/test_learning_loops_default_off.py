"""Learning loops are off in the shipped default — DEF-01 (FR-45).

Three loops let an attacker who can reach the scanner influence what the
scanner later does:

* the vault stores detected attacks and matches future input against them,
* the auto-tuner moves detector thresholds from observed outcomes,
* the threat feed pulls signatures from a remote source.

FR-45 requires all three off unless an operator turns them on. The feed must
additionally refuse to run unverified rather than warning and continuing.
"""

from __future__ import annotations

import pytest

from cosmac.config import load_config


@pytest.fixture
def shipped_default() -> dict:
    """The configuration a user gets with no config file of their own."""
    return load_config()["cosmac"]


class TestShippedDefaults:
    def test_vault_auto_store_is_off(self, shipped_default):
        vault = shipped_default.get("vault", {})
        assert vault.get("auto_store_detections") is False, (
            "the vault must not learn from traffic by default (FR-45)"
        )

    def test_feedback_auto_tune_is_off(self, shipped_default):
        feedback = shipped_default.get("feedback", {})
        assert feedback.get("auto_tune") is False, (
            "thresholds must not move on their own by default (FR-45)"
        )

    def test_threat_feed_sync_is_off(self, shipped_default):
        feed = shipped_default.get("threat_feed", {})
        assert feed.get("enabled") is False and feed.get("auto_sync") is False, (
            "the threat feed must not sync by default (FR-45)"
        )

    def test_no_default_feed_url(self, shipped_default):
        """REP-08: the upstream feed URL must not ship as a default."""
        feed = shipped_default.get("threat_feed", {})
        assert not feed.get("feed_url"), (
            "a default feed URL points COSMAC at a third party's content"
        )


class TestNoDatabaseWorkOnDefaultScan:
    def test_scan_opens_no_autotuner_connection(self, tmp_path, monkeypatch):
        """DEF-01: with defaults, a scan must not touch the tuning database."""
        import sqlite3

        from cosmac.engine import CosmacEngine

        opened: list[str] = []
        real_connect = sqlite3.connect

        def recording_connect(target, *args, **kwargs):
            opened.append(str(target))
            return real_connect(target, *args, **kwargs)

        engine = CosmacEngine(
            config_dict={
                "cosmac": {
                    "detectors": {"d022_semantic_classifier": {"enabled": False}},
                    "vault": {"enabled": False},
                }
            },
            data_dir=str(tmp_path),
        )
        monkeypatch.setattr(sqlite3, "connect", recording_connect)
        engine.scan("What is the weather today?")

        tuning_hits = [p for p in opened if "tuning" in p.lower()]
        assert not tuning_hits, (
            f"auto-tuner opened a connection per scan with defaults: {tuning_hits}"
        )


class TestFeedRefusesUnverified:
    def test_sync_without_key_raises(self, tmp_path):
        """DEF-01: no silent fall-back to the unverified path."""
        from cosmac.engine import CosmacEngine

        engine = CosmacEngine(
            config_dict={
                "cosmac": {
                    "detectors": {"d022_semantic_classifier": {"enabled": False}},
                    "vault": {"enabled": False},
                }
            },
            data_dir=str(tmp_path),
        )
        with pytest.raises((ValueError, RuntimeError), match=r"(?i)verif|key"):
            engine.sync_threats(feed_url="https://example.invalid/feed.json")

    def test_sync_with_no_url_raises(self, tmp_path):
        from cosmac.engine import CosmacEngine

        engine = CosmacEngine(
            config_dict={
                "cosmac": {
                    "detectors": {"d022_semantic_classifier": {"enabled": False}},
                    "vault": {"enabled": False},
                }
            },
            data_dir=str(tmp_path),
        )
        with pytest.raises((ValueError, RuntimeError)):
            engine.sync_threats()
