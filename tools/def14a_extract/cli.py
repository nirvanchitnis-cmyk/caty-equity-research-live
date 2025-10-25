"""Typer CLI wiring for def14a tools with optional dependency support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .api import get_def14a_facts
from .models import FactRequest

try:  # pragma: no cover - optional dependency handler
    import typer
except ImportError:  # pragma: no cover - optional dependency handler
    typer = None  # type: ignore


def _build_app() -> "typer.Typer | None":
    if not typer:
        return None

    app = typer.Typer(
        help="DEF 14A fact extraction tool suite",
        no_args_is_help=True,
    )

    @app.callback(invoke_without_command=True)
    def main(ctx: "typer.Context") -> None:  # type: ignore[name-defined]
        """DEF 14A fact extraction tool suite."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

    @app.command("facts")
    def facts_command(  # type: ignore[annotation-unchecked]
        ticker: Optional[str] = typer.Option(None, help="Ticker symbol"),
        cik: Optional[str] = typer.Option(None, help="CIK"),
        year: Optional[int] = typer.Option(None, help="Filing year"),
        facts: Optional[List[str]] = typer.Option(None, help="Comma-separated fact ids"),
        provenance: bool = typer.Option(False, "--provenance", help="Include provenance output"),
        output: Optional[Path] = typer.Option(None, "--output", help="Optional output path"),
        refresh: bool = typer.Option(False, "--refresh", help="Bypass cache"),
    ) -> None:
        fact_list = facts or []
        expanded: List[str] = []
        for item in fact_list:
            expanded.extend([part.strip() for part in item.split(",") if part.strip()])

        request = FactRequest(
            ticker=ticker,
            cik=cik,
            year=year,
            facts=expanded or None,
            include_provenance=provenance,
            output_path=output,
            refresh=refresh,
        )
        results = get_def14a_facts(request)
        serializable = {key: vars(value) for key, value in results.items()}
        payload = json.dumps(serializable, indent=2)
        if output:
            output.write_text(payload)
            typer.echo(f"Wrote facts to {output}")
        else:
            typer.echo(payload)

    return app


app = _build_app()


def cli_main() -> None:
    if not app:
        raise RuntimeError(
            "Typer is required for CLI usage. Install with `pip install typer`."
        )
    app()  # type: ignore[operator]


if __name__ == "__main__":  # pragma: no cover - manual invocation path
    cli_main()
