# matched-randtest

`matched-randtest` performs exact one-sided randomization tests for a binary outcome in independent matched blocks. It is a `src/`-layout Python package for Python 3.10 or newer.

## Installation

```bash
pip install git+https://github.com/fc2651/matched-randtest.git
```

For plotting:

```bash
pip install "matched-randtest[plot]@git+https://github.com/fc2651/matched-randtest.git"
```

The exact statistical core has no third-party runtime dependencies.

## Worked example

```python
from matched_randtest import Block, randomization_test

blocks = [
    Block(i, 6, 3, y, x)
    for i, (y, x) in enumerate(
        zip(
            [4, 3, 5, 2, 4, 3, 5, 2],
            [3, 2, 3, 1, 2, 2, 3, 1],
        )
    )
]

result = randomization_test(blocks, alternative="increase")
print(result.p_value)  # Fraction(1128, 15625), 0.072192
print(result.tail_assignment_count)
print(result.total_assignment_count)
```

For the optional plot, pass the `TestResult` (not only the distribution) so the selected tail can be highlighted:

```python
from matched_randtest import plot_null_distribution

ax = plot_null_distribution(result)
```

Run the included example:

```bash
python examples/worked_example.py
```

Run the lightweight benchmark:

```bash
python benchmarks/benchmark.py
```

## Assumptions and interpretation

Each `Block(n=N, m=m, y=y, x=x)` states that a block has `N` participants, exactly `m` are assigned to treatment, `y` participants have success outcomes, and `x` of the treated participants have successes. Every subset of `m` participants is equally likely to receive treatment within a block, and blocks are independent.

The exact p-value is for Fisher's global sharp null: treatment assignment changes no participant's outcome. It is **not** appropriate for observationally matched data or arbitrary assignment mechanisms. The package does not accept eligibility restrictions, forbidden allocations, non-uniform probabilities, or cross-block balance constraints.

Supported alternatives are:

- `"increase"`: inclusive right tail `T >= T_obs`;
- `"decrease"`: inclusive left tail `T <= T_obs`.

The result preserves integer assignment counts. `p_value` is a `fractions.Fraction`, while `p_value_float` is only a convenience conversion.
