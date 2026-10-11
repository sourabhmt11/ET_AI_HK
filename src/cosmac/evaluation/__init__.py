"""Evaluation harness — spec section 10, backlog epic EVL.

Public surface:

* :mod:`cosmac.evaluation.schema` — the sample record (EVL-01), its
  loader and the independence checker.
* :mod:`cosmac.evaluation.metrics` — Wilson intervals; every rate is a
  :class:`~cosmac.evaluation.metrics.Proportion`.
* :mod:`cosmac.evaluation.runner` — the evaluation command's engine
  (EVL-02) and the reliability report writer.
"""

from cosmac.evaluation.metrics import Proportion, wilson_interval
from cosmac.evaluation.runner import (
    ClassifierUnavailableError,
    EvalResult,
    run_evaluation,
    write_report,
)
from cosmac.evaluation.schema import (
    ATTACK_FAMILIES,
    SOURCE_TYPES,
    TRUST_TIERS,
    EvalSample,
    SchemaError,
    check_independence,
    load_samples,
)

__all__ = [
    "ATTACK_FAMILIES",
    "SOURCE_TYPES",
    "TRUST_TIERS",
    "ClassifierUnavailableError",
    "EvalResult",
    "EvalSample",
    "Proportion",
    "SchemaError",
    "check_independence",
    "load_samples",
    "run_evaluation",
    "wilson_interval",
    "write_report",
]
