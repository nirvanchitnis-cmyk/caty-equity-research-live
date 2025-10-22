# CATY Deposit Beta Regressions (Quarterly Δ vs Fed Funds Δ)

Method: OLS of quarterly change in product deposit rates vs change in effective Fed Funds.

| Product | Beta | Std Err | t | R^2 | N | Notes |
|---|---:|---:|---:|---:|---:|---|
| time_deposits | 0.8686 | 0.2150 | 4.04 | 0.6711 | 10 |  |
| money_market | 0.4071 | 0.1315 | 3.10 | 0.5451 | 10 |  |
| savings | -0.0572 | 0.1478 | -0.39 | 0.0184 | 10 |  |
| ib_demand | 0.3253 | 0.1158 | 2.81 | 0.4964 | 10 |  |
| interest_bearing_total | 0.6261 | 0.1720 | 3.64 | 0.6235 | 10 |  |
| all_in_total | 0.1210 | 0.0380 | 3.18 | 0.5589 | 10 |  |

Sources: data/deposit_beta_history.json (SEC 10-Q MD&A tables), data/fed_funds_quarterly.csv (FRED FEDFUNDS quarterly average).