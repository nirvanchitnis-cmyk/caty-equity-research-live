"""
Probability-Weighted Valuation Analysis
Reconciles regression vs normalized earnings with market-implied probabilities
"""

# Scenario targets
target_current = 56.42  # Regression at ROTE 11.95%
target_normalized = 39.32  # Gordon Growth at ROTE 10.21%
current_price = 45.87

# Analyst probability assessment
prob_current = 0.60
prob_normalized = 0.40

# Expected value
expected_target = (prob_current * target_current) + (prob_normalized * target_normalized)
expected_return = ((expected_target - current_price) / current_price) * 100

# Market-implied probabilities
market_prob_current = (current_price - target_normalized) / (target_current - target_normalized)
market_prob_normalized = 1 - market_prob_current

print(f"Analyst Weighted (60/40): ${expected_target:.2f} ({expected_return:+.1f}%)")
print(f"Market Implied (38/62): ${current_price:.2f} (current)")
print(f"\nRating: HOLD (expected return +8% in neutral range)")
print(f"\nKey: Market already prices 62% normalization probability")
