"""Typer-based CLI for IR materials fact extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .pipeline import extract_facts_from_url
from .discovery import discover_ir_artifacts

try:  # pragma: no cover - optional dependency guard
    import typer
except ImportError:  # pragma: no cover
    typer = None  # type: ignore

try:  # pragma: no cover - optional dependency guard
    from rich.console import Console
    from rich.table import Table as RichTable
except ImportError:  # pragma: no cover
    Console = None  # type: ignore
    RichTable = None  # type: ignore


def _build_app() -> "typer.Typer | None":
    if not typer or not Console or not RichTable:
        return None

    console = Console()
    app = typer.Typer(
        help="IR Materials Extraction Toolkit",
        no_args_is_help=True,
    )

    def _parse_fact_ids(raw: str) -> List[str]:
        if not raw:
            return []
        parts: List[str] = []
        for chunk in raw.split(","):
            value = chunk.strip()
            if value:
                parts.append(value)
        return parts

    def _render_table(payload: dict) -> None:
        table = RichTable(title="Extracted Facts")
        table.add_column("Fact ID", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Confidence", style="yellow")
        for fact_id, detail in payload.items():
            value = detail.get("value")
            if isinstance(value, (int, float)):
                value_str = f"{value:,.2f}"
            else:
                value_str = str(value)
            confidence = detail.get("confidence")
            conf_str = f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "—"
            table.add_row(fact_id, value_str, conf_str)
        console.print(table)

    @app.callback(invoke_without_command=True)
    def main(ctx: "typer.Context") -> None:  # type: ignore[name-defined]
        """IR materials extraction toolkit."""
        if ctx.invoked_subcommand is None:
            console.print(ctx.get_help())
            raise typer.Exit(0)

    @app.command("facts")
    def facts_command(  # type: ignore[annotation-unchecked]
        url: Optional[str] = typer.Option(None, help="Direct URL to an IR artifact"),
        ticker: Optional[str] = typer.Option(None, help="Ticker symbol to drive discovery"),
        period: Optional[str] = typer.Option(None, help="Period qualifier, e.g., Q2-2025"),
        facts: str = typer.Option("", help="Comma-separated fact IDs to extract"),
        output: Optional[Path] = typer.Option(None, help="Optional output JSON path"),
        provenance: bool = typer.Option(True, help="Include provenance metadata"),
        refresh: bool = typer.Option(False, help="Force refresh (bypass cache)"),
    ) -> None:
        if not url and not ticker:
            console.print("[red]Error: Must provide --url or --ticker[/red]")
            raise typer.Exit(1)

        resolved_url = url
        if ticker and not resolved_url:
            console.print(f"[blue]Discovering IR artifacts for {ticker}...[/blue]")
            try:
                candidates = discover_ir_artifacts(ticker, period)
            except Exception as exc:  # pragma: no cover - network errors
                console.print(f"[red]Discovery failed: {exc}[/red]")
                raise typer.Exit(1)
            if not candidates:
                console.print(f"[yellow]No artifacts found for {ticker}[/yellow]")
                raise typer.Exit(1)
            resolved_url = candidates[0]
            console.print(f"[green]Using {resolved_url}[/green]")

        fact_ids = _parse_fact_ids(facts) or None

        console.print(f"[blue]Extracting facts from {resolved_url}...[/blue]")
        try:
            fact_map = extract_facts_from_url(
                resolved_url,
                fact_ids=fact_ids,
                force_refresh=refresh,
            )
        except Exception as exc:
            console.print(f"[red]Extraction failed: {exc}[/red]")
            raise typer.Exit(1)

        if not fact_map:
            console.print("[yellow]No facts extracted[/yellow]")
            raise typer.Exit(0)

        payload: dict = {}
        for fact_id, candidate in fact_map.items():
            record = {
                "value": candidate.value,
                "value_type": candidate.value_type,
                "unit": candidate.unit,
                "confidence": candidate.confidence,
            }
            if provenance:
                record.update(
                    {
                        "source_url": candidate.source_url,
                        "file_sha256": candidate.file_sha256,
                        "method": candidate.method,
                        "table_id": candidate.table_id,
                        "page_numbers": candidate.page_numbers,
                        "validation": candidate.validation,
                    }
                )
            payload[fact_id] = record

        if output:
            output.write_text(json.dumps(payload, indent=2))
            console.print(f"[green]Wrote {len(payload)} facts to {output}[/green]")
        else:
            _render_table(payload)
            console.print("\n[bold]JSON Output:[/bold]")
            console.print_json(data=payload)

    @app.command("discover")
    def discover_command(  # type: ignore[annotation-unchecked]
        ticker: str = typer.Argument(..., help="Ticker symbol"),
        period: Optional[str] = typer.Option(None, help="Period qualifier (e.g., Q2-2025)"),
        save_index: Optional[Path] = typer.Option(None, help="Write discovered URLs to JSON"),
    ) -> None:
        console.print(f"[blue]Discovering IR artifacts for {ticker}...[/blue]")
        try:
            candidates = discover_ir_artifacts(ticker, period)
        except Exception as exc:  # pragma: no cover - network errors
            console.print(f"[red]Discovery failed: {exc}[/red]")
            raise typer.Exit(1)

        if not candidates:
            console.print("[yellow]No artifacts found[/yellow]")
            raise typer.Exit(1)

        console.print(f"[green]Found {len(candidates)} artifact(s):[/green]")
        for index, candidate in enumerate(candidates, start=1):
            console.print(f"  {index}. {candidate}")

        if save_index:
            payload = {
                "ticker": ticker,
                "period": period,
                "urls": candidates,
            }
            save_index.write_text(json.dumps(payload, indent=2))
            console.print(f"[green]Saved index to {save_index}[/green]")

    return app


app = _build_app()


def main() -> None:
    if not app:
        raise RuntimeError(
            "Typer and Rich are required for CLI usage. Install with `pip install typer rich`."
        )
    app()  # type: ignore[operator]


__all__ = ["app", "main"]


if __name__ == "__main__":  # pragma: no cover
    main()
