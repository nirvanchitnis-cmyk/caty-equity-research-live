import pytest

# Ensure optional dependencies are present for CLI tests
pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner  # type: ignore  # noqa: E402

from tools.ir_materials_extract.cli import app  # noqa: E402


runner = CliRunner()


def test_cli_help_displays_usage() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "IR Materials Extraction Toolkit" in result.stdout


def test_facts_command_requires_source() -> None:
    result = runner.invoke(app, ["facts"])
    assert result.exit_code == 1
    assert "Must provide --url or --ticker" in result.stdout
