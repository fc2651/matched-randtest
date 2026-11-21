# `matched-randtest` Design Specification

**For the coding agent implementing the course project**

## Goal and intended users

Build a small, installable Python package for exact one-sided randomization tests of a binary outcome in a matched-block randomized experiment. The primary users are students and researchers analyzing experiments whose treatment assignments followed the randomization design supplied to the package.

The package answers whether the observed number of successes assigned to treatment is unusually high or low under Fisher's global sharp null: treatment assignment changes no participant's outcome. It is not for observationally matched data, and it must not imply that matching alone makes an observational analysis randomized.

The checkpoint MVP is the one-treatment-versus-control package described below. The three-arm method is a planned depth extension, not a checkpoint requirement or a promise to implement it if it proves too large or insufficiently distinct from prior coursework.

## Randomization assumptions and statistical method

### MVP design

There are independent blocks indexed by `i`. Block `i` has:

- `N_i` participants;
- exactly `m_i` participants assigned to treatment;
- `y_i` observed successes among all participants; and
- `x_i` observed successes among treated participants.

Within each block, every subset of exactly `m_i` participants is equally likely to be treated. Assignments are independent across blocks. Block sizes and treated counts may differ across blocks. The outcome is binary and is held fixed under the global sharp null.

The test statistic is:

`T = sum_i x_i`

For a block, the assignment count for `x` treatment successes is:

`w_i(x) = choose(y_i, x) * choose(N_i - y_i, m_i - x)`

for:

`max(0, m_i - (N_i - y_i)) <= x <= min(y_i, m_i)`.

The block's total assignment count is `choose(N_i, m_i)`. Combine block contributions with a dynamic program (DP) of integer assignment counts. If `D_i(t)` is the number of assignments in the first `i` blocks yielding total `t`, update:

`D_i(t + x) += D_(i-1)(t) * w_i(x)`.

The final probability at `T=t` is `D(t) / product_i choose(N_i, m_i)`. Use integer counts throughout; do not enumerate all complete assignments in production and do not use floating-point convolution for the exact result.

The two supported alternatives are:

- `"increase"`: inclusive right tail `T >= T_obs`;
- `"decrease"`: inclusive left tail `T <= T_obs`.

The exact p-value is the tail assignment count divided by the total assignment count. Preserve both integer counts in the result and expose the p-value as `fractions.Fraction`; a float convenience value may be derived from it. The observed assignment is included in either tail.

### Three-arm depth extension

If implemented after the MVP, support two treatment arms (`A`, `B`) and one control arm (`C`). In each block, arm counts `m_A`, `m_B`, and `m_C` are fixed and sum to `N`. Every labeled allocation of participants to these arm counts is equally likely within a block, independently across blocks. Binary outcomes are fixed under the global sharp null that assignment to any arm has no effect on any participant.

For block `i`, let `s_A`, `s_B`, `s_C` be successes assigned to the arms, with `s_A+s_B+s_C=y_i` and `0 <= s_j <= m_j`. The number of assignments for that success allocation is:

`multinomial(y_i; s_A, s_B, s_C) * multinomial(N_i-y_i; m_A-s_A, m_B-s_B, m_C-s_C)`.

The block denominator is `N_i! / (m_A! m_B! m_C!)`. Use a sparse two-dimensional DP keyed by cumulative `(T_A, T_B)` integer counts. The total number of successes across all arms, `Y=sum_i y_i`, is fixed, so `T_C=Y-T_A-T_B`. Define directional contrasts:

- `D_A = T_A - T_C`;
- `D_B = T_B - T_C`.

For the one-sided omnibus question “does either treatment arm increase success versus control?”, use `Q=max(D_A,D_B)` and the inclusive p-value `P(Q >= Q_obs)`.

Return the observed contrasts and one-sided marginal p-values for `D_A` and `D_B`, plus single-step max-statistic adjusted p-values computed from the joint exact distribution:

- `p_adj,A = P(Q >= D_A,obs)`;
- `p_adj,B = P(Q >= D_B,obs)`.

Also return the omnibus p-value. State prominently that these exact p-values are for the global sharp null. The max-statistic adjustment does **not** by itself establish strong family-wise error control when only one arm's sharp null is true; do not make that claim.

Validate this extension against direct enumeration for tiny designs. Enumerate every labeled arm allocation within each block, combine blocks, and compare the complete joint `(T_A,T_B)` assignment-count table, denominator, observed contrasts, omnibus tail, marginal tails, and adjusted tails against the DP. Include cases with ties and boundary arm counts. If state growth or implementation burden is not manageable, leave this extension unimplemented and document the MVP as complete.

## Input and validation

Use typed, dependency-free Python records as the primary API; do not require pandas. Define an immutable `Block` record with:

- `block_id`: unique hashable identifier;
- `n`: block size `N_i`;
- `m`: treated count `m_i`;
- `y`: total successes `y_i`;
- `x`: observed treated successes `x_i`.

The input is a nonempty sequence of `Block` records. Reject malformed records and invalid values explicitly. In particular:

- `n`, `m`, `y`, and `x` must be Python integers; reject booleans and floats, including integral-valued floats;
- `n >= 1`, `0 <= m <= n`, and `0 <= y <= n`;
- `x` must lie in the feasible range `max(0, m-(n-y)) <= x <= min(y,m)`;
- block IDs must be hashable and unique.

Treat `m=0` and `m=n` as valid boundary designs. Do not infer or accept arbitrary randomization rules from data. Raise clear `TypeError` or `ValueError` exceptions for invalid input; do not silently drop blocks or repair values.

For the three-arm extension, define a separate typed block record with `n`, the three arm counts, `y`, and observed successes in all three arms. Validate that arm counts sum to `n`, observed arm successes sum to `y`, and each arm's success and failure counts are feasible. Do not accept eligibility restrictions, forbidden allocations, non-uniform probabilities, or cross-block balance constraints.

## MVP public interface and outputs

Use a `src/` package layout. The import package should be `matched_randtest` (distribution/project name `matched-randtest`). Keep the public API small and cohesive:

1. `Block` — immutable block-summary input record.
2. `validate_blocks(blocks)` — validate the design and observed assignment, raising on invalid input.
3. `exact_null_distribution(blocks)` — return the exact count distribution and diagnostics.
4. `randomization_test(blocks, alternative="increase")` — return the complete exact test result.
5. `plot_null_distribution(result, ax=None)` — plot the exact distribution, mark `T_obs`, and highlight the selected tail; return the axes and do not implicitly display or save the figure.

The distribution result should include:

- observed statistic `T_obs`;
- `assignment_counts`, a mapping from each attainable total `T` to its integer count;
- total assignment count, equal to `product_i choose(n_i,m_i)`;
- per-block assignment counts mapping feasible `x_i` values to `w_i(x_i)`;
- peak DP support size, defined as the largest number of nonzero statistic keys after processing any block;
- cumulative DP states visited, defined as the sum of the number of nonzero statistic keys after each block (excluding the initial empty prefix).

The test result should include the full distribution result, alternative, tail description, tail assignment-count numerator, total assignment-count denominator, exact `Fraction` p-value, and a concise method/assumption description. Probabilities are exactly represented by each integer count over the common denominator; a probability mapping may be provided as a derived convenience, but must not replace the integer counts.

Plotting is part of the MVP but Matplotlib is an optional dependency. Keep the exact statistical core standard-library-only. Provide a plotting extra such as `pip install matched-randtest[plot]`; importing or using the core must work without Matplotlib. If plotting is requested without the extra, raise a clear installation-oriented error.

## Stretch goals and explicit non-goals

**Primary stretch goal:** implement the three-arm extension above, including joint DP, omnibus inference, marginal results, max-statistic adjustment, brute-force comparisons, and explicit global-sharp-null limitations. It is not needed to meet the checkpoint.

**Low-priority stretch goal:** add a normal-approximation p-value for the one-treatment MVP only. If attempted, approximate the exact statistic with a normal distribution whose mean and variance are sums of the independent block hypergeometric means and variances. Apply a 0.5 continuity correction to the inclusive one-sided tail (`T_obs - 0.5` for increase; `T_obs + 0.5` for decrease). If the variance is zero, report that the approximation is unavailable with a clear reason; never substitute a misleading numeric approximation. Label and report the approximation method and correction separately from the exact result.

For each block, use `p_i=y_i/n_i`, `mu_i=m_i*p_i`, and, when `n_i>1`, `var_i=m_i*p_i*(1-p_i)*(n_i-m_i)/(n_i-1)`; use zero variance when `n_i=1`. Sum these moments across blocks.

Two-sided tests are out of scope for the MVP. Do not choose or imply a two-sided convention until a later design decision addresses the competing exact two-sided definitions. Restricted/forbidden assignments, non-uniform assignment probabilities, global balance constraints, and arbitrary randomization designs are out of scope; do not claim support for them.

## Correctness, tests, and performance

Use `pytest`. Required tests include:

- Independently enumerate all assignments in tiny one-treatment designs and compare every DP assignment count and probability with enumeration.
- Verify DP counts sum to `product_i choose(n_i,m_i)` and probabilities sum exactly to one.
- Verify inclusive increase/decrease tail counts and p-values, including ties at `T_obs`.
- Test no-success and all-success blocks, `m=0`, `m=n`, unequal block sizes, unequal treated counts, one block, invalid values, and incompatible observed assignments.
- Test the worked example below exactly.
- Test plotting's marker and highlighted tail, and test the missing-optional-dependency error without making Matplotlib a core dependency.
- Keep runtime tests out of timing-sensitive unit-test assertions; use a reproducible benchmark script for measurements.

The supplied worked example is consistent with the specification:

- 8 blocks, `n=6`, `m=3`;
- `y=[4,3,5,2,4,3,5,2]`, `x=[3,2,3,1,2,2,3,1]`;
- `T_obs=17`, total assignment count `20^8 = 25,600,000,000`;
- inclusive increase-tail count `1,848,115,200`;
- exact p-value `1,848,115,200 / 25,600,000,000 = 0.072192`.

Benchmark representative increasing designs, recording runtime, peak memory where practical, peak/cumulative DP states, blocks, and attainable statistic support. Avoid brittle performance assertions in tests. Do not promise a universal maximum problem size: document measured configurations and the cost drivers, and let the sparse DP use available resources rather than inventing an arbitrary hard-coded limit.

## Documentation and installation

Document:

- the randomization assumptions and sharp-null interpretation;
- why this package is not for observational matched data;
- the distinction between treatment assignment counts and participant counts;
- the meaning and limitations of an exact p-value;
- supported alternatives, inclusive-tail convention, exact count denominator, and result fields;
- the limits on unsupported designs and the three-arm global-null scope if that extension is implemented.

Provide runnable examples using `Block` records, including the worked example. Include a plotting example that installs the optional extra.

Use `pyproject.toml` and a conventional `src/` layout. Target Python 3.10 or newer unless project environment constraints require otherwise. Initially support installation from the public GitHub repository, for example `pip install git+https://github.com/<owner>/matched-randtest.git`; PyPI publication is a stretch goal, not required. Add GitHub Actions checks for supported Python versions on Windows, macOS, and Linux, covering tests and package installation. Keep the exact core free of third-party runtime dependencies; use Matplotlib only in the optional plot extra and pytest as a development dependency.

## Project-size and coursework-distinctness assessment

The MVP has a distinct statistical target from a sum of independent Bernoulli variables: it conditions on fixed observed outcomes and follows each block's without-replacement random assignment mechanism, giving hypergeometric assignment counts and a design-based sharp-null reference distribution. However, both projects combine discrete block contributions using convolution/DP. That is a real algorithmic overlap, not something to obscure with extra wrapper functions.

Its validation, exact integer arithmetic, robust API, plotting, cross-platform packaging, exhaustive tests, and performance work add engineering substance but do not eliminate the shared convolution structure. The three-arm joint DP is a well-bounded and feasible depth extension: it changes the state from one statistic to a joint two-statistic distribution and enables a max-statistic adjustment. Its sparse state space can grow much faster than the one-dimensional MVP, so benchmark it before committing to completion.

## Four-week checkpoint milestones

1. **Week 1 — package/API and validation:** establish the package skeleton, `Block`, validation, user-facing errors, and tests for feasible/infeasible inputs.
2. **Week 2 — exact MVP core:** implement block assignment counts and integer DP; expose exact distribution and one-sided result; pass brute-force and invariant tests, including the supplied example.
3. **Week 3 — usable package:** add plotting extra, result documentation, examples, and edge-case tests.
4. **Week 4 — checkpoint demonstration:** finalize installation from the public GitHub repository, cross-platform CI, runnable example, and benchmark report with state counts and runtime (memory where practical). Demonstrate the complete one-treatment MVP.

Only after the checkpoint MVP is complete should work begin on the three-arm primary stretch goal. Attempt the normal approximation only after that and only if time remains.
