"""
Probability-Weighted Valuation Analysis
Reconciles regression vs normalized earnings with market-implied probabilities
"""

import json
from pathlib import Path

# Load current market data from single source of truth
_data_path = Path(__file__).parent.parent / 'data' / 'market_data_current.json'
with open(_data_path, 'r') as f:
    _market_data = json.load(f)

# Scenario targets
target_current = 56.50  # Regression at ROTE 12.35% (7-peer: EWBC, CVBF, HAFC, COLB, WAFD, PPBI, BANC)
target_normalized = 39.32  # Gordon Growth at ROTE 10.21%
current_price = _market_data['price']  # DYNAMIC: loaded from data/market_data_current.json


def expected_return(prob_current: float) -> float:
    prob_normalized = 1 - prob_current
    expected_target = (prob_current * target_current) + (prob_normalized * target_normalized)
    return ((expected_target - current_price) / current_price) * 100


# Probability anchors
data_prob_current = 0.85  # Post-2008 breach frequency (15.7% tail)
upper_prob_current = 0.74  # 95% upper bound using Wilson interval for post-2008 sample
market_prob_current = (current_price - target_normalized) / (target_current - target_normalized)


def describe(label: str, prob_current: float) -> str:
    prob_normalized = 1 - prob_current
    exp_target = prob_current * target_current + prob_normalized * target_normalized
    exp_return = expected_return(prob_current)
    return (
        f"{label:>22}: P(Current)={prob_current:5.1%}, P(Normalized)={prob_normalized:5.1%}, "
        f"Target=${exp_target:5.2f}, Return={exp_return:+5.1f}%"
    )


hurdle_return = 15.0
prob_for_hurdle = (hurdle_return / 100 + 1) * current_price
prob_for_hurdle = (prob_for_hurdle - target_normalized) / (target_current - target_normalized)

print(describe("Data-Anchored", data_prob_current))
print(describe("95% Upper Bound", upper_prob_current))
print(describe("Market-Implied", market_prob_current))
print(describe("Neutral 60/40", 0.60))

print("\nBUY hurdle (expected return > +15%): requires P(Current) >= "
      f"{prob_for_hurdle:5.1%} (tail <= {(1 - prob_for_hurdle):5.1%})")
