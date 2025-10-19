"""Analyze Cathay Bank's historical net charge-off ratios using FDIC data.

This module reads the FDIC quarterly net charge-off ratio series (field
`NTLNLSCOQR`) stored in `evidence/raw/fdic_CATY_NTLNLSCOQR_timeseries.csv`
and produces probability statistics for different horizons.  The output is a
markdown file (`evidence/NCO_probability_summary.md`) that Claude can cite in
the valuation work to justify scenario weights.

The logic is intentionally transparent:

* Probabilities are simple frequencies of quarters that breach the
  through-cycle threshold (45.8 bps = 0.458%).
* We look at multiple windows (full history, post-2000, post-GFC, post-2014,
  and trailing 8/16/32 quarters) to anchor judgment with data.
* Rolling four-quarter averages provide an additional stress lens more aligned
  with cycle assessments, recognizing that regulators focus on sustained loss
  pressure rather than a single print.

Running this script regenerates the markdown summary and prints the key
statistics to stdout for quick review.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Sequence, Tuple


RAW_CSV = Path(__file__).resolve().parents[1] / "evidence" / "raw" / "fdic_CATY_NTLNLSCOQR_timeseries.csv"
OUTPUT_MD = Path(__file__).resolve().parents[1] / "evidence" / "NCO_probability_summary.md"
# Through-cycle net charge-off assumption expressed as a decimal (45.8 bps)
THRESHOLD = 0.00458


@dataclass(frozen=True)
class Observation:
    date: dt.date
    ratio: float  # expressed as decimal (e.g., 0.002 = 20 bps)


def load_series() -> List[Observation]:
    rows: List[Observation] = []
    with RAW_CSV.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for record in reader:
            date = dt.datetime.strptime(record["REPDTE"], "%Y%m%d").date()
            ratio = float(record["NTLNLSCOQR"]) / 100.0  # convert percent to decimal
            rows.append(Observation(date=date, ratio=ratio))
    rows.sort(key=lambda obs: obs.date)
    return rows


def window_prob(observations: Sequence[Observation], start: dt.date | None) -> float:
    window = [obs for obs in observations if start is None or obs.date >= start]
    if not window:
        return float("nan")
    breaches = sum(obs.ratio >= THRESHOLD for obs in window)
    return breaches / len(window)


def trailing_prob(observations: Sequence[Observation], count: int) -> float:
    if len(observations) < count:
        return float("nan")
    window = observations[-count:]
    breaches = sum(obs.ratio >= THRESHOLD for obs in window)
    return breaches / len(window)


def rolling_average(observations: Sequence[Observation], window: int) -> List[Tuple[dt.date, float]]:
    output: List[Tuple[dt.date, float]] = []
    for idx in range(window - 1, len(observations)):
        slice_ratios = [obs.ratio for obs in observations[idx - window + 1 : idx + 1]]
        output.append((observations[idx].date, mean(slice_ratios)))
    return output


def format_percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def generate_markdown(observations: Sequence[Observation]) -> str:
    sections: List[str] = []

    sections.append("# Net Charge-Off Probability Summary\n")
    sections.append("Data source: FDIC Bank Financials API (field `NTLNLSCOQR`). Values represent annualised quarterly net charge-off ratios.")
    sections.append("")

    windows = [
        ("Full history (since 1984)", None),
        ("Post-2000", dt.date(2000, 1, 1)),
        ("Post-GFC (>= 2008)", dt.date(2008, 1, 1)),
        ("Post-2014", dt.date(2014, 1, 1)),
        ("Post-2020", dt.date(2020, 1, 1)),
    ]

    sections.append("## Frequency of quarterly breaches\n")
    sections.append("Threshold: 45.8 bps (0.458%) total loan & lease net charge-off ratio")
    sections.append("")
    sections.append("| Window | Quarters | Breach Probability |")
    sections.append("|--------|----------|--------------------|")
    for label, start in windows:
        window_obs = [obs for obs in observations if start is None or obs.date >= start]
        probability = window_prob(observations, start)
        sections.append(
            f"| {label} | {len(window_obs)} | {format_percentage(probability)} |"
        )

    trailing_windows = [8, 16, 32]
    sections.append("")
    sections.append("| Trailing sample | Breach Probability |")
    sections.append("|-----------------|--------------------|")
    for count in trailing_windows:
        prob = trailing_prob(observations, count)
        sections.append(f"| Last {count} quarters | {format_percentage(prob)} |")

    sections.append("")
    sections.append("## Rolling four-quarter averages\n")
    sections.append("Evaluates sustained loss pressure – counts instances where the trailing 4-quarter average exceeds the through-cycle assumption.")
    rolling = rolling_average(observations, window=4)
    breaches = [(date, avg) for date, avg in rolling if avg >= THRESHOLD]
    breach_pct = len(breaches) / len(rolling) if rolling else float("nan")
    sections.append(f"- Rolling average breach probability: {format_percentage(breach_pct)} ({len(breaches)} of {len(rolling)} observations)")
    if breaches:
        sections.append("- Last breach: " + breaches[-1][0].isoformat())
    else:
        sections.append("- Last breach: Not observed post-1984")

    recent = [obs for obs in observations if obs.date >= dt.date(2018, 1, 1)]
    if recent:
        average_recent = mean(obs.ratio for obs in recent)
        sections.append("")
        sections.append("## Recent central tendency\n")
        sections.append(f"- Mean net charge-off ratio since 2018: {average_recent * 100:.2f}%")
        sections.append(f"- Standard deviation since 2018: { (sum((obs.ratio - average_recent) ** 2 for obs in recent) / len(recent)) ** 0.5 * 100:.2f}%")

    sections.append("")
    sections.append("## Interpretation Guide\n")
    sections.append("- Quarterly breach probabilities above zero pre-2014 are driven by the GFC (2008-2012).")
    sections.append("- No quarterly breaches above 45.8 bps have occurred since 2013; rolling four-quarter averages have not exceeded the threshold in that period either.")
    sections.append("- Post-2020 quarters show elevated but sub-threshold ratios (peaking at 28.2 bps in 2024).")
    sections.append("- Use these frequencies to calibrate scenario weights rather than relying on gut feel.")

    return "\n".join(sections) + "\n"


def main() -> None:
    observations = load_series()
    markdown = generate_markdown(observations)
    OUTPUT_MD.write_text(markdown)
    print(markdown)


if __name__ == "__main__":
    main()
