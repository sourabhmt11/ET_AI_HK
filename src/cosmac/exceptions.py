"""Custom exceptions for cosmac."""

from __future__ import annotations


class CosmacError(Exception):
    """Base exception for all cosmac errors."""


class ConfigError(CosmacError):
    """Raised when configuration is invalid or cannot be loaded."""


class DetectorError(CosmacError):
    """Raised when a detector fails during scanning."""


class RegistryError(CosmacError):
    """Raised when detector registration or discovery fails."""


class VaultError(CosmacError):
    """Raised when the attack vault encounters an error."""


class EmbedderError(CosmacError):
    """Raised when embedding generation fails."""


class PersistenceError(CosmacError):
    """Raised when database operations fail."""


class FeedbackError(CosmacError):
    """Raised when feedback recording or processing fails."""


class ThreatFeedError(CosmacError):
    """Raised when threat feed import/export/sync fails."""


class ScanError(CosmacError):
    """Raised when a scan operation fails."""


class BenchmarkError(CosmacError):
    """Raised when a benchmark operation fails."""
