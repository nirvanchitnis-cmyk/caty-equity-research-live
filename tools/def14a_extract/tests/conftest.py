import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


@pytest.fixture
def sample_fact_request():
    return {
        "ticker": "CATY",
        "year": 2024,
        "facts": ["meeting_date"],
    }
