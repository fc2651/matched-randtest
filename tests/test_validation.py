import pytest

from matched_randtest import Block, validate_blocks


def test_accepts_boundary_and_unequal_blocks():
    blocks = (
        Block("control", 4, 0, 2, 0),
        Block("treated", 5, 5, 3, 3),
        Block("mixed", 6, 2, 4, 2),
    )
    assert validate_blocks(blocks) == blocks


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("n", True),
        ("n", 3.0),
        ("m", True),
        ("y", 2.5),
        ("x", False),
    ],
)
def test_rejects_booleans_and_floats(field, value):
    values = {"n": 4, "m": 2, "y": 2, "x": 1}
    values[field] = value
    with pytest.raises(TypeError, match="Python int"):
        validate_blocks([Block("b", **values)])


@pytest.mark.parametrize(
    "block",
    [
        Block("bad-n", 0, 0, 0, 0),
        Block("bad-m", 3, -1, 1, 0),
        Block("bad-m", 3, 4, 1, 1),
        Block("bad-y", 3, 1, -1, 0),
        Block("bad-y", 3, 1, 4, 1),
        Block("bad-x", 4, 2, 1, 2),
    ],
)
def test_rejects_invalid_ranges(block):
    with pytest.raises(ValueError):
        validate_blocks([block])


def test_rejects_malformed_and_duplicate_ids():
    with pytest.raises(ValueError, match="at least one"):
        validate_blocks([])
    with pytest.raises(TypeError, match="Block"):
        validate_blocks([object()])
    with pytest.raises(TypeError, match="hashable"):
        validate_blocks([Block([], 2, 1, 1, 1)])
    with pytest.raises(ValueError, match="duplicate"):
        validate_blocks([Block("same", 2, 1, 1, 1), Block("same", 3, 1, 1, 1)])
