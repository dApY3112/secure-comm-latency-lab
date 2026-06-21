"""Command-line interface for Secure Communication Latency Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from secure_comm_latency_lab.analysis.plots import generate_plots
from secure_comm_latency_lab.analysis.report import generate_report
from secure_comm_latency_lab.analysis.summarize import summarize_jsonl
from secure_comm_latency_lab.config import LabConfig, load_config
from secure_comm_latency_lab.runners import DirectRunner, TorRunner, WireGuardRunner
from secure_comm_latency_lab.utils.commands import check_optional_tools
from secure_comm_latency_lab.utils.logging import get_console
from secure_comm_latency_lab.utils.time import timestamp_for_filename

app = typer.Typer(
    help="Ethical latency measurements for direct, WireGuard, and Tor SOCKS paths.",
    no_args_is_help=True,
)
console = get_console()


def _build_runners(config: LabConfig, network_profile: str):
    if config.paths.direct.enabled:
        yield DirectRunner(config, network_profile)
    if config.paths.wireguard.enabled:
        yield WireGuardRunner(config, network_profile)
    if config.paths.tor.enabled:
        yield TorRunner(config, network_profile)


def _run_experiment(config: LabConfig, output_path: Path | None = None) -> Path:
    output_dir = config.experiment.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_path or (
        output_dir / f"{config.experiment.name}_{timestamp_for_filename()}.jsonl"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with destination.open("w", encoding="utf-8") as handle:
        for profile in config.active_profiles():
            for repetition in range(config.experiment.repetitions):
                console.print(
                    f"Running profile={profile.name} repetition={repetition + 1}/"
                    f"{config.experiment.repetitions}"
                )
                for runner in _build_runners(config, profile.name):
                    for result in runner.run_once():
                        handle.write(result.to_json_line())
                        count += 1

    console.print(f"[green]Wrote {count} measurement records to {destination}[/green]")
    return destination


@app.command()
def check() -> None:
    """Report optional system tool availability."""
    table = Table(title="Optional dependency check")
    table.add_column("Tool")
    table.add_column("Available")
    table.add_column("Path")
    table.add_column("Feature")
    for status in check_optional_tools():
        table.add_row(
            status.name,
            "yes" if status.available else "no",
            status.path or "-",
            status.feature,
        )
    console.print(table)
    console.print(
        "Missing optional tools disable only their related measurements; analysis still works."
    )


@app.command("run")
def run_command(
    config: Path = typer.Option(..., "--config", "-c", help="YAML experiment config."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Optional JSONL output path."),
) -> None:
    """Run an experiment and write JSONL measurements."""
    try:
        lab_config = load_config(config)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    if lab_config.network_conditions.enabled:
        console.print(
            "[yellow]network_conditions.enabled labels profiles only; apply tc netem "
            "separately with scripts/setup_netem.sh after reviewing commands.[/yellow]"
        )
    _run_experiment(lab_config, output)


@app.command()
def summarize(
    input: Path = typer.Option(..., "--input", "-i", help="Input JSONL measurement file."),
    output: Path = typer.Option(..., "--output", "-o", help="Output summary CSV."),
) -> None:
    """Summarize JSONL measurements into grouped CSV statistics."""
    try:
        summary = summarize_jsonl(input, output)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Wrote {len(summary)} summary rows to {output}[/green]")


@app.command()
def plot(
    summary: Path = typer.Option(..., "--summary", "-s", help="Summary CSV path."),
    output: Path = typer.Option(..., "--output", "-o", help="Output figure directory."),
) -> None:
    """Generate matplotlib figures from a summary CSV."""
    try:
        figures = generate_plots(summary, output)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    if figures:
        for figure in figures:
            console.print(f"[green]Wrote {figure}[/green]")
    else:
        console.print("[yellow]No figures generated; summary did not contain plottable metrics.[/yellow]")


@app.command()
def report(
    summary: Path = typer.Option(..., "--summary", "-s", help="Summary CSV path."),
    figures: Path = typer.Option(..., "--figures", "-f", help="Figure directory."),
    output: Path = typer.Option(..., "--output", "-o", help="Output Markdown report."),
) -> None:
    """Generate a Markdown report."""
    try:
        report_path = generate_report(summary_path=summary, figures_dir=figures, output_path=output)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Wrote {report_path}[/green]")


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
