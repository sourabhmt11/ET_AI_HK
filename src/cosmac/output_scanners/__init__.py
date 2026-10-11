"""Output scanners — analyse LLM-generated text for harmful content.

Nine scanners ship in the box: :class:`ToxicityScanner`,
:class:`CodeInjectionScanner`, :class:`PromptLeakageScanner`,
:class:`OutputPIIScanner`, :class:`SchemaValidationScanner`,
:class:`BiasFairnessOutputScanner`, :class:`SentimentOutputScanner`,
:class:`HallucinationOutputScanner`, and :class:`RelevanceScanner`.

Use :class:`OutputScanEngine` to run all of them (or a named subset) in
one call and get back an aggregated :class:`OutputScanReport`.
"""

from cosmac.output_scanners.base import BaseOutputScanner
from cosmac.output_scanners.bias_fairness import BiasFairnessOutputScanner
from cosmac.output_scanners.code_injection import CodeInjectionScanner
from cosmac.output_scanners.engine import OutputScanEngine, available_scanners
from cosmac.output_scanners.hallucination import HallucinationOutputScanner
from cosmac.output_scanners.models import OutputScanReport, OutputScanResult
from cosmac.output_scanners.output_pii import OutputPIIScanner
from cosmac.output_scanners.prompt_leakage import PromptLeakageScanner
from cosmac.output_scanners.relevance import RelevanceScanner
from cosmac.output_scanners.schema_validation import SchemaValidationScanner
from cosmac.output_scanners.sentiment import SentimentOutputScanner
from cosmac.output_scanners.toxicity import ToxicityScanner

__all__ = [
    "BaseOutputScanner",
    "BiasFairnessOutputScanner",
    "CodeInjectionScanner",
    "HallucinationOutputScanner",
    "OutputPIIScanner",
    "OutputScanEngine",
    "OutputScanReport",
    "OutputScanResult",
    "PromptLeakageScanner",
    "RelevanceScanner",
    "SchemaValidationScanner",
    "SentimentOutputScanner",
    "ToxicityScanner",
    "available_scanners",
]
