import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner  # type: ignore  # noqa: E402

from tools.def14a_extract.cli import app
from tools.def14a_extract.models import FactWithProvenance


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "DEF 14A fact extraction tool suite" in result.stdout


def test_cli_facts_command_writes_output(monkeypatch, tmp_path):
    output_path = tmp_path / "facts.json"

    fake_fact = FactWithProvenance(
        value="2025-05-15",
        value_type="date",
        unit=None,
        fiscal_year=2025,
        issuer_cik="0000123456",
        filing_accession="0000123456-25-000001",
        source_url="https://example.com/def14a",
        file_sha256="abc123",
        page_numbers=[5],
        dom_path=None,
        table_id=None,
        method="regex",
        confidence=0.92,
        validation={"warnings": []},
    )

    def _fake_get_facts(request):  # type: ignore[unused-argument]
        return {"meeting_date": fake_fact}

    monkeypatch.setattr("tools.def14a_extract.cli.get_def14a_facts", _fake_get_facts)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "facts",
            "--ticker",
            "CATY",
            "--facts",
            "meeting_date",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    payload = output_path.read_text()
    assert '"meeting_date"' in payload
    assert '"2025-05-15"' in payload
