from matched_randtest import Block, plot_null_distribution, randomization_test


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
print(f"T_obs = {result.distribution.T_obs}")
print(f"tail count = {result.tail_assignment_count}")
print(f"denominator = {result.total_assignment_count}")
print(f"p-value = {result.p_value} = {result.p_value_float}")

# Optional: pip install matched-randtest[plot]
# plot_null_distribution(result)
