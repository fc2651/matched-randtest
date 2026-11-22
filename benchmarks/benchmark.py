"""Reproducible lightweight benchmark for exact one-dimensional DP."""

import platform
import sys
from statistics import median
from time import perf_counter

from matched_randtest import Block, exact_null_distribution


REPEATS = 7


def run(name: str, blocks: list[Block]) -> None:
    runtimes = []
    result = None
    for _ in range(REPEATS):
        start = perf_counter()
        result = exact_null_distribution(blocks)
        runtimes.append(perf_counter() - start)

    assert result is not None
    print(
        f"{name}: blocks={len(blocks)} "
        f"attainable_support={len(result.assignment_counts)} "
        f"peak_dp_support={result.peak_dp_support_size} "
        f"cumulative_dp_states={result.cumulative_dp_states_visited} "
        f"denominator={result.total_assignment_count} "
        f"denominator_digits={len(str(result.total_assignment_count))} "
        f"median_runtime_seconds={median(runtimes):.6f} "
        f"repeats={REPEATS}"
    )


print(f"python={sys.version.split()[0]}")
print(f"platform={platform.platform()}")

worked_example = [
    Block(i, 6, 3, y, x)
    for i, (y, x) in enumerate(
        zip(
            [4, 3, 5, 2, 4, 3, 5, 2],
            [3, 2, 3, 1, 2, 2, 3, 1],
        )
    )
]
run("worked-example", worked_example)

unequal = []
for i in range(12):
    n = 3 + i % 5
    m = 1 + i % 3
    y = 1 + i % 4
    x = max(0, m - (n - y))
    unequal.append(Block(i, n=n, m=m, y=y, x=x))
run("increasing-unequal", unequal)


def deterministic_design(block_count: int) -> list[Block]:
    blocks = []
    for i in range(block_count):
        n = 6 + i % 3
        m = 2 + i % 4
        y = 1 + (i * 3) % (n - 1)
        minimum_x = max(0, m - (n - y))
        maximum_x = min(y, m)
        x = minimum_x + (i % (maximum_x - minimum_x + 1))
        blocks.append(Block(i, n=n, m=m, y=y, x=x))
    return blocks


run("deterministic-50", deterministic_design(50))
run("deterministic-200", deterministic_design(200))
