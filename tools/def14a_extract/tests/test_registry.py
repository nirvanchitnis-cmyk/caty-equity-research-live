from tools.def14a_extract.registry import load_registry


def test_registry_loads():
    registry = load_registry()
    assert "meeting_date" in registry
    assert len(registry) >= 25
