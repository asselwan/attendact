"""Risk band to intervention variant trigger logic. Phase 2."""

DEFAULT_RULES = {
    "very_high": {"send": True, "variant": "smart"},
    "high": {"send": True, "variant": "simple_confirmation"},
    "moderate": {"send": False},
    "low": {"send": False},
}
