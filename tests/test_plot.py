import builtins
import pytest

from matched_randtest import (
    Block,
    exact_null_distribution,
    plot_null_distribution,
    randomization_test,
)


def test_plot_requires_test_result():
    distribution = exact_null_distribution([Block("a", 4, 2, 2, 1)])
    with pytest.raises(TypeError, match="TestResult"):
        plot_null_distribution(distribution)


def test_missing_matplotlib_error(monkeypatch):
    real_import = builtins.__import__

    def import_without_matplotlib(name, *args, **kwargs):
        if name == "matplotlib.pyplot" or name.startswith("matplotlib"):
            raise ImportError("matplotlib intentionally unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_matplotlib)
    result = randomization_test([Block("a", 4, 2, 2, 1)])

    with pytest.raises(ImportError, match=r"matched-randtest\[plot\]"):
        plot_null_distribution(result)


def test_plot_marks_observed_and_tail():
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    result = randomization_test(
        [Block("a", 4, 2, 2, 1)],
        alternative="increase",
    )
    ax = plot_null_distribution(result)

    assert ax.lines
    assert ax.lines[0].get_xdata()[0] == result.distribution.T_obs
    assert len(ax.patches) == len(result.distribution.assignment_counts)
    bar_colors = {tuple(patch.get_facecolor()) for patch in ax.patches}
    assert len(bar_colors) >= 2
    plt.close(ax.figure)


def test_plot_highlights_decrease_tail():
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba

    result = randomization_test(
        [Block("a", 4, 2, 2, 1)],
        alternative="decrease",
    )
    ax = plot_null_distribution(result)
    colors_by_statistic = {
        int(patch.get_x() + patch.get_width() / 2): tuple(patch.get_facecolor())
        for patch in ax.patches
    }

    tail_color = to_rgba("tab:red")
    assert colors_by_statistic[result.distribution.T_obs] == tail_color
    assert any(color != tail_color for color in colors_by_statistic.values())
    plt.close(ax.figure)
