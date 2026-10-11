"""cosmac: Self-learning prompt injection detection engine."""

from cosmac.engine import CosmacEngine
from cosmac.models import (
    Action,
    DetectionResult,
    MatchDetail,
    ScanContext,
    ScanReport,
    Severity,
    ThreatEntry,
    ThreatFeed,
    ToolProvenance,
    ToolResultAttackFamily,
)
from cosmac.tool_guard import ToolResultGuard, scan_tool_result

__version__ = "0.8.1"

__all__ = [
    "Action",
    "DetectionResult",
    "MatchDetail",
    "CosmacEngine",
    "ScanContext",
    "ScanReport",
    "Severity",
    "ThreatEntry",
    "ThreatFeed",
    "ToolProvenance",
    "ToolResultAttackFamily",
    "ToolResultGuard",
    "__version__",
    "scan_tool_result",
]
