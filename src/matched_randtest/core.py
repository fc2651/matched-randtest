"""Exact one-treatment-versus-control randomization inference."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb
from collections.abc import Hashable, Mapping, Sequence
from typing import Any


@dataclass(frozen=True)
class Block:
    """Immutable summary of one independently randomized block."""

    block_id: Hashable
    n: int
    m: int
    y: int
    x: int


@dataclass(frozen=True)
class DistributionResult:
    """Exact null distribution and dynamic-programming diagnostics."""

    T_obs: int
    assignment_counts: Mapping[int, int]
    total_assignment_count: int
    per_block_assignment_counts: Mapping[Hashable, Mapping[int, int]]
    peak_dp_support_size: int
    cumulative_dp_states_visited: int

    @property
    def probabilities(self) -> Mapping[int, Fraction]:
        """Derived exact probabilities."""
        return {
            statistic: Fraction(count, self.total_assignment_count)
            for statistic, count in self.assignment_counts.items()
        }


@dataclass(frozen=True)
class TestResult:
    """One-sided exact randomization test result."""

    distribution: DistributionResult
    alternative: str
    tail_description: str
    tail_assignment_count: int
    total_assignment_count: int
    p_value: Fraction
    method: str

    @property
    def p_value_float(self) -> float:
        """Convenience floating-point view of the exact p-value."""
        return float(self.p_value)


def _require_python_int(name: str, value: Any) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a Python int; booleans and floats are not allowed")


def validate_blocks(blocks: Sequence[Block]) -> tuple[Block, ...]:
    """Validate and return an immutable tuple of block records."""

    if isinstance(blocks, (str, bytes)) or not isinstance(blocks, Sequence):
        raise TypeError("blocks must be a nonempty sequence of Block records")
    if len(blocks) == 0:
        raise ValueError("blocks must contain at least one Block")

    validated: list[Block] = []
    seen_ids: set[Hashable] = set()

    for index, block in enumerate(blocks):
        if not isinstance(block, Block):
            raise TypeError(f"blocks[{index}] must be a Block record")

        for name in ("n", "m", "y", "x"):
            _require_python_int(f"blocks[{index}].{name}", getattr(block, name))

        try:
            hash(block.block_id)
        except (TypeError, AttributeError) as exc:
            raise TypeError(f"blocks[{index}].block_id must be hashable") from exc

        if block.block_id in seen_ids:
            raise ValueError(f"duplicate block_id: {block.block_id!r}")
        seen_ids.add(block.block_id)

        if block.n < 1:
            raise ValueError(f"blocks[{index}].n must be at least 1")
        if not 0 <= block.m <= block.n:
            raise ValueError(f"blocks[{index}].m must satisfy 0 <= m <= n")
        if not 0 <= block.y <= block.n:
            raise ValueError(f"blocks[{index}].y must satisfy 0 <= y <= n")

        minimum_x = max(0, block.m - (block.n - block.y))
        maximum_x = min(block.y, block.m)
        if not minimum_x <= block.x <= maximum_x:
            raise ValueError(
                f"blocks[{index}].x must satisfy "
                f"{minimum_x} <= x <= {maximum_x}"
            )

        validated.append(block)

    return tuple(validated)


def exact_null_distribution(blocks: Sequence[Block]) -> DistributionResult:
    """Return the exact integer assignment-count distribution under the sharp null."""

    checked = validate_blocks(blocks)
    dp: dict[int, int] = {0: 1}
    peak_support = 1
    cumulative_states = 0
    per_block_counts: dict[Hashable, Mapping[int, int]] = {}
    total_assignment_count = 1

    for block in checked:
        block_counts: dict[int, int] = {}
        minimum_x = max(0, block.m - (block.n - block.y))
        maximum_x = min(block.y, block.m)

        for x in range(minimum_x, maximum_x + 1):
            block_counts[x] = (
                comb(block.y, x) * comb(block.n - block.y, block.m - x)
            )

        per_block_counts[block.block_id] = dict(block_counts)
        next_dp: dict[int, int] = {}
        for current_total, current_count in dp.items():
            for x, block_count in block_counts.items():
                statistic = current_total + x
                next_dp[statistic] = (
                    next_dp.get(statistic, 0)
                    + current_count * block_count
                )

        dp = next_dp
        support_size = len(dp)
        peak_support = max(peak_support, support_size)
        cumulative_states += support_size
        total_assignment_count *= comb(block.n, block.m)

    if sum(dp.values()) != total_assignment_count:
        raise RuntimeError("internal error: DP assignment counts do not match denominator")

    T_obs = sum(block.x for block in checked)
    return DistributionResult(
        T_obs=T_obs,
        assignment_counts=dict(sorted(dp.items())),
        total_assignment_count=total_assignment_count,
        per_block_assignment_counts=per_block_counts,
        peak_dp_support_size=peak_support,
        cumulative_dp_states_visited=cumulative_states,
    )


def randomization_test(
    blocks: Sequence[Block],
    alternative: str = "increase",
) -> TestResult:
    """Run an exact one-sided randomization test under the global sharp null."""

    if alternative not in ("increase", "decrease"):
        raise ValueError("alternative must be either 'increase' or 'decrease'")

    distribution = exact_null_distribution(blocks)
    if alternative == "increase":
        tail_count = sum(
            count
            for statistic, count in distribution.assignment_counts.items()
            if statistic >= distribution.T_obs
        )
        tail_description = f"one-sided inclusive right tail: T >= {distribution.T_obs}"
    else:
        tail_count = sum(
            count
            for statistic, count in distribution.assignment_counts.items()
            if statistic <= distribution.T_obs
        )
        tail_description = f"one-sided inclusive left tail: T <= {distribution.T_obs}"

    return TestResult(
        distribution=distribution,
        alternative=alternative,
        tail_description=tail_description,
        tail_assignment_count=tail_count,
        total_assignment_count=distribution.total_assignment_count,
        p_value=Fraction(tail_count, distribution.total_assignment_count),
        method=(
            "Exact design-based randomization test under the global sharp null "
            "that treatment assignment has no effect on outcomes."
        ),
    )


def plot_null_distribution(result: TestResult, ax: Any | None = None) -> Any:
    """Plot a test's exact null distribution and selected tail; Matplotlib is optional."""

    if not isinstance(result, TestResult):
        raise TypeError("result must be a TestResult")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Plotting requires the optional Matplotlib dependency; "
            "install it with 'pip install matched-randtest[plot]'"
        ) from exc

    if ax is None:
        _, ax = plt.subplots()

    distribution = result.distribution
    statistics = sorted(distribution.assignment_counts)
    counts = [distribution.assignment_counts[t] for t in statistics]
    probabilities = [
        Fraction(count, distribution.total_assignment_count) for count in counts
    ]
    y_values = [float(value) for value in probabilities]

    colors = ["tab:blue"] * len(statistics)
    for index, statistic in enumerate(statistics):
        if (
            result.alternative == "increase"
            and statistic >= distribution.T_obs
        ) or (
            result.alternative == "decrease"
            and statistic <= distribution.T_obs
        ):
            colors[index] = "tab:red"

    ax.bar(statistics, y_values, width=0.8, color=colors)
    ax.axvline(
        distribution.T_obs,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"T_obs = {distribution.T_obs}",
    )
    ax.set_xlabel("T")
    ax.set_ylabel("Exact probability")
    ax.set_title("Exact null distribution")
    ax.legend()
    return ax
