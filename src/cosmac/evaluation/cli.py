"""`cosmac eval` command group — EVL-02 (Appendix C #15).

Registered on the main CLI by ``cosmac.cli``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from cosmac.evaluation.runner import (
    ClassifierUnavailableError,
    run_evaluation,
    write_report,
)
from cosmac.evaluation.schema import SchemaError, check_independence, load_samples


@click.group("eval")
def eval_group() -> None:
    """Run evaluation sets and produce reliability reports."""


@eval_group.command("run")
@click.option(
    "--set",
    "set_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSONL sample set in the EVL-01 schema.",
)
@click.option(
    "--out",
    "out_dir",
    default="eval-out",
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory for results.json and report.md.",
)
@click.option(
    "--allow-missing-classifier",
    is_flag=True,
    help=(
        "Run even if d022 did not load. The report records the classifier as "
        "unavailable; the figures are NOT comparable with a normal run."
    ),
)
def eval_run(set_path: Path, out_dir: Path, allow_missing_classifier: bool) -> None:
    """Run a sample set through the shipped default configuration."""
    try:
        result = run_evaluation(set_path, require_classifier=not allow_missing_classifier)
    except ClassifierUnavailableError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(2)
    except SchemaError as exc:
        click.echo(f"error: invalid sample set: {exc}", err=True)
        sys.exit(2)

    json_path, report_path = write_report(result, out_dir)

    click.echo("")
    click.echo(f"  Attack detection : {result.attack_overall.format()}")
    click.echo(f"  Benign block rate: {result.benign_block_rate.format()}")
    click.echo("")
    click.echo(f"  results : {json_path}")
    click.echo(f"  report  : {report_path}")
    click.echo("")
    if not result.header["classifier_loaded"]:
        click.echo(
            "  WARNING: the ML classifier was not loaded. These figures "
            "understate detection and must not be compared with a normal run.",
            err=True,
        )


@eval_group.command("check")
@click.option(
    "--set",
    "set_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSONL sample set to validate.",
)
def eval_check(set_path: Path) -> None:
    """Validate a sample set against the EVL-01 schema and report independence."""
    try:
        samples = load_samples(set_path)
    except SchemaError as exc:
        click.echo(f"invalid: {exc}", err=True)
        sys.exit(1)

    report = check_independence(samples)
    click.echo(f"valid: {set_path}")
    click.echo(report.summary())

    for label, groups in (
        ("payload", report.shared_payload_groups),
        ("carrier", report.shared_carrier_groups),
    ):
        for key, ids in list(groups.items())[:10]:
            click.echo(f"  shared {label} {key!r}: {', '.join(ids)}")

    if not report.is_fully_independent:
        click.echo(
            "\nnote: samples sharing a payload or carrier are not independent "
            "observations (spec 10.1); the gate counts must use the "
            "independent totals above."
        )
