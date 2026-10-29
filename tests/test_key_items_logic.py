"""Logic tests for key item placement. No ROM needed.

    python -m pytest tests/test_key_items_logic.py
or  python tests/test_key_items_logic.py
"""
import random
import sys
import types
from pathlib import Path

# import randoglobin.key_items without pulling in the Qt GUI through randoglobin/__init__.py
_pkg = types.ModuleType("randoglobin")
_pkg.__path__ = [str(Path(__file__).resolve().parent.parent / "randoglobin")]
sys.modules.setdefault("randoglobin", _pkg)

from randoglobin import key_items as K  # noqa: E402

ALL = [item.key for item in K.ITEM_LIST]


def test_vanilla_is_beatable():
    vanilla = {loc.key: loc.vanilla for loc in K.LOCATIONS}
    assert K.is_beatable(K.LOCATIONS, vanilla)


def test_every_seed_is_beatable_and_complete():
    for seed in range(300):
        placement = K.place_key_items(random.Random(seed), ALL, K.LOCATIONS)
        assert K.is_beatable(K.LOCATIONS, placement), seed
        assert sorted(placement.values()) == sorted(ALL), seed  # each item exactly once


def test_unshuffled_items_stay_vanilla():
    shuffled = ["key_r", "key_g", "key_b", "badges"]
    for seed in range(50):
        placement = K.place_key_items(random.Random(seed), shuffled, K.LOCATIONS)
        for loc in K.LOCATIONS:
            if loc.vanilla not in shuffled:
                assert placement[loc.key] == loc.vanilla


def test_items_never_locked_behind_themselves():
    for seed in range(100):
        placement = K.place_key_items(random.Random(seed), ALL, K.LOCATIONS)
        for loc in K.LOCATIONS:
            assert placement[loc.key] not in loc.requires


def test_optional_slots_are_used():
    # an extra slot reachable from the start lets anything move into it (once vanilla spots
    # are allowed to receive filler instead)
    extra = K.sidequest_locations([("test_slot", "Test", [])])
    locations = K.LOCATIONS + extra
    seen = set()
    for seed in range(300):
        placement = K.place_key_items(random.Random(seed), ALL, locations, allow_empty_vanilla=True)
        assert K.is_beatable(locations, placement)
        if "test_slot" in placement:
            seen.add(placement["test_slot"])
    assert len(seen) > 3


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
