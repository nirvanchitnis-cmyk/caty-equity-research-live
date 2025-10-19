# Net Charge-Off Probability Summary

Data source: FDIC Bank Financials API (field `NTLNLSCOQR`). Values represent annualised quarterly net charge-off ratios.

## Frequency of quarterly breaches

Threshold: 45.8 bps (0.458%) total loan & lease net charge-off ratio

| Window | Quarters | Breach Probability |
|--------|----------|--------------------|
| Full history (since 1984) | 166 | 13.3% |
| Post-2000 | 102 | 12.7% |
| Post-GFC (>= 2008) | 70 | 15.7% |
| Post-2014 | 46 | 0.0% |
| Post-2020 | 22 | 0.0% |

| Trailing sample | Breach Probability |
|-----------------|--------------------|
| Last 8 quarters | 0.0% |
| Last 16 quarters | 0.0% |
| Last 32 quarters | 0.0% |

## Rolling four-quarter averages

Evaluates sustained loss pressure – counts instances where the trailing 4-quarter average exceeds the through-cycle assumption.
- Rolling average breach probability: 13.5% (22 of 163 observations)
- Last breach: 2012-03-31

## Recent central tendency

- Mean net charge-off ratio since 2018: 0.05%
- Standard deviation since 2018: 0.09%

## Interpretation Guide

- Quarterly breach probabilities above zero pre-2014 are driven by the GFC (2008-2012).
- No quarterly breaches above 45.8 bps have occurred since 2013; rolling four-quarter averages have not exceeded the threshold in that period either.
- Post-2020 quarters show elevated but sub-threshold ratios (peaking at 28.2 bps in 2024).
- Use these frequencies to calibrate scenario weights rather than relying on gut feel.
