# Lightweight exact-DP benchmark

- Command: `python benchmarks/benchmark.py`
- Python: 3.13.14
- Platform: Windows 11 (`Windows-11-10.0.26200-SP0`)
- Repetitions: 7 per design; runtime is the median.

| Design | Blocks | Attainable support | Peak DP support | Cumulative DP states | Denominator digits | Median runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| Worked example | 8 | 17 | 17 | 82 | 11 | 0.000030 |
| Unequal blocks | 12 | 12 | 12 | 101 | 10 | 0.000033 |
| Deterministic | 50 | 88 | 88 | 2,267 | 71 | 0.000636 |
| Deterministic | 200 | 355 | 355 | 35,743 | 283 | 0.011163 |

The script prints each denominator as an exact integer. Cumulative DP states are
the sum of the nonzero support sizes after each block; this is a support-size
diagnostic, not the number of DP transitions or a general performance guarantee.
These measurements describe this environment and these designs only.
