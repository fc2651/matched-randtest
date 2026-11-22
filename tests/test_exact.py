from collections import Counter
from fractions import Fraction
from itertools import combinations, product
from math import comb

import pytest

from matched_randtest import (
    Block,
    exact_null_distribution,
    randomization_test,
)


def enumerate_assignments(blocks):
    block_assignments = []
    for block in blocks:
        treated_assignments = []
        success_positions = set(range(block.y))
        for treated in combinations(range(block.n), block.m):
            treated_set = set(treated)
            x = len(success_positions.intersection(treated_set))
            treated_assignments.append((x, treated))
        block_assignments.append(treated_assignments)

    counts = Counter()
    for allocations in product(*block_assignments):
        counts[sum(x for x, _ in allocations)] += 1
    return counts


@pytest.mark.parametrize(
    "blocks",
    [
        (Block("a", 3, 1, 2, 1),),
        (Block("a", 4, 2, 2, 1), Block("b", 3, 1, 1, 1)),
        (Block("a", 2, 0, 1, 0), Block("b", 3, 3, 2, 2)),
        (Block("a", 1, 1, 1, 1),),
    ],
)
def test_dp_matches_independent_brute_force(blocks):
    result = exact_null_distribution(blocks)
    enumerated = enumerate_assignments(blocks)

    assert dict(result.assignment_counts) == dict(sorted(enumerated.items()))
    assert sum(result.assignment_counts.values()) == result.total_assignment_count
    assert sum(
        (Fraction(count, result.total_assignment_count)
         for count in result.assignment_counts.values()),
        Fraction(0),
    ) == Fraction(1)

    denominator = 1
    for block in blocks:
        denominator *= comb(block.n, block.m)
    assert result.total_assignment_count == denominator


@pytest.mark.parametrize("alternative", ["increase", "decrease"])
def test_inclusive_tails_match_enumeration(alternative):
    blocks = (
        Block("a", 4, 2, 3, 2),
        Block("b", 3, 1, 1, 0),
    )
    enumerated = enumerate_assignments(blocks)
    observed = sum(block.x for block in blocks)
    tail = (
        sum(count for statistic, count in enumerated.items() if statistic >= observed)
        if alternative == "increase"
        else
        sum(count for statistic, count in enumerated.items() if statistic <= observed)
    )
    result = randomization_test(blocks, alternative)

    assert result.distribution.T_obs == observed
    assert result.tail_assignment_count == tail
    assert result.p_value == Fraction(tail, result.total_assignment_count)


def test_ties_are_included():
    blocks = (Block("a", 3, 1, 1, 1),)
    enumerated = enumerate_assignments(blocks)
    for alternative in ("increase", "decrease"):
        result = randomization_test(blocks, alternative)
        tail_count = sum(
            count
            for statistic, count in enumerated.items()
            if (statistic >= 1 if alternative == "increase" else statistic <= 1)
        )
        assert result.tail_assignment_count == tail_count


def test_worked_example_exact():
    blocks = tuple(
        Block(i, 6, 3, y, x)
        for i, (y, x) in enumerate(
            zip(
                [4, 3, 5, 2, 4, 3, 5, 2],
                [3, 2, 3, 1, 2, 2, 3, 1],
            )
        )
    )
    result = randomization_test(blocks, "increase")

    assert result.distribution.T_obs == 17
    assert result.total_assignment_count == 20**8
    assert result.total_assignment_count == 25_600_000_000
    assert result.tail_assignment_count == 1_848_115_200
    assert result.p_value == Fraction(1_848_115_200, 25_600_000_000)
    assert result.p_value_float == 0.072192
    assert sum(result.distribution.assignment_counts.values()) == 20**8


def test_block_weights_match_enumeration():
    block = Block("a", 5, 2, 3, 1)
    result = exact_null_distribution([block])
    assert result.per_block_assignment_counts["a"] == {
        0: comb(3, 0) * comb(2, 2),
        1: comb(3, 1) * comb(2, 1),
        2: comb(3, 2) * comb(2, 0),
    }


def test_no_success_all_success_and_boundary_assignments():
    blocks = (
        Block("none", 4, 2, 0, 0),
        Block("all", 3, 1, 3, 1),
        Block("control", 5, 0, 2, 0),
        Block("all-treated", 5, 5, 2, 2),
    )
    result = exact_null_distribution(blocks)

    assert sum(result.assignment_counts.values()) == result.total_assignment_count
    assert result.T_obs == 3
    assert set(result.assignment_counts) == {3}


def test_rejects_invalid_alternative():
    with pytest.raises(ValueError, match="alternative"):
        randomization_test([Block("a", 2, 1, 1, 1)], alternative="two-sided")
