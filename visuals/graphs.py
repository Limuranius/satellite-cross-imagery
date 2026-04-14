import abc
import os
import pathlib
from collections import namedtuple

import pandas as pd
from matplotlib.widgets import Slider
from sklearn.linear_model import LinearRegression

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress, gaussian_kde

import utils


def relplot_with_linregress(
        x: pd.Series | np.ndarray,
        y: pd.Series | np.ndarray,
        ax=None,
        s=1,
        fit_intercept=True,
        sample_size=10000,
        xlabel=None,
        ylabel=None,
        round_slope=2,
        round_intercept=2,
        round_r2=3,
        draw_line=True,
        color_density=True,
        draw_diagonal=False,
        robust=False,
):
    if ax is None:
        ax = plt.subplot()
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    data = pd.DataFrame({"x": x, "y": y})

    # Calculating linear regression
    # lin = LinearRegression(fit_intercept=fit_intercept)
    # lin.fit(data[["x"]], data["y"])
    # slope = lin.coef_[0]
    # intercept = lin.intercept_
    # r2 = lin.score(data[["x"]], data["y"])
    lin = utils.linregress_report(
        data["x"],
        data["y"],
        use_intercept=fit_intercept,
        robust=robust,
    )
    slope = lin["slope"]
    intercept = lin["intercept"]
    if intercept is None:
        intercept = 0.0
    r2 = lin["R^2"]

    # Calculate the point density
    data = data.sample(n=min(len(data), sample_size), random_state=42)  # Sampling data, so it fits on plot
    x = data["x"]
    y = data["y"]
    if color_density:
        xy = np.vstack([x, y])
        z = gaussian_kde(xy)(xy)
        ax.scatter(x, y, c=z, s=s)
    else:
        ax.scatter(x, y, s=s)

    if fit_intercept:
        txt = f"""slope={round(slope, round_slope)} ± {round(lin["slope_interv"], round_slope)}
intercept={round(intercept, round_intercept)}
r^2={round(r2, round_r2)}
"""
    else:
        txt = f"""slope={round(slope, round_slope)} ± {round(lin["slope_interv"], round_slope)}
r^2={round(r2, round_r2)}
"""

    if draw_line:
        ax.plot(x, x * slope + intercept, color="red")
    if draw_diagonal:
        ax.plot(
            [x.min(), x.max()],
            [x.min(), x.max()],
            color=(0, 0, 0, 0.5),
            linestyle="--",
        )
    ax.grid(alpha=0.7)

    ax.text(
        0,
        0.99,
        txt,
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes,
    )


def scatter_with_density(x, y, ax):
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    ax.scatter(x, y, c=z, s=1)


def boxplot_with_stats(x, ax):
    ax.boxplot(x, vert=False)
    txt = f"""mean={np.mean(x):.5f}
median={np.median(x):.5f}
std={np.std(x):.5f}"""
    ax.text(
        0,
        0.99,
        txt,
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes,
    )


def save_fig_to_path(path: pathlib.Path):
    if not path.parent.exists():
        os.makedirs(path.parent, exist_ok=True)
    plt.savefig(path)
    plt.close()


class InteractivePlot(abc.ABC):
    SliderData = namedtuple("SliderData", ["name", "start", "end", "init", "step"])
    sliders: list[SliderData]  # must be initialized
    _sliders_data: dict[str, Slider]  # name: Slider

    def __init__(self, s=2):
        self.fig, self.ax = plt.subplots()
        plt.grid()
        self.fig.subplots_adjust(left=0.25)
        self._sliders_data = dict()
        self.scatter = self.ax.scatter([0], [0], s=s)
        self.line = self.ax.plot([0], [0], color="black", lw=2)[0]

        for i, slider_data in enumerate(self.sliders):
            slider = Slider(
                ax=self.fig.add_axes([0.05, 0.04 * i, 0.2, 0.05]),
                label=slider_data.name,
                valmin=slider_data.start,
                valmax=slider_data.end,
                valinit=slider_data.init,
                valstep=slider_data.step,
            )
            self._sliders_data[slider_data.name] = slider
            slider.on_changed(self._update)
        self._update(0)
        plt.show()

    def _update(self, _):
        values = {name: slider.val for name, slider in self._sliders_data.items()}
        self.update(values)

    def update(self, values: dict):
        pass


class InteractiveImshow(abc.ABC):
    SliderData = namedtuple("SliderData", ["name", "start", "end", "init", "step"])
    sliders: list[SliderData]  # must be initialized
    _sliders_data: dict[str, Slider]  # name: Slider

    def __init__(self, starting_image: np.ndarray, vmin=None, vmax=None, cmap=None):
        self.fig, self.ax = plt.subplots()
        self.fig.subplots_adjust(left=0.25)
        self._sliders_data = dict()
        self.imshow = self.ax.imshow(starting_image, vmin=vmin, vmax=vmax, cmap=cmap)

        for i, slider_data in enumerate(self.sliders):
            slider = Slider(
                ax=self.fig.add_axes([0.05, 0.04 * i, 0.2, 0.05]),
                label=slider_data.name,
                valmin=slider_data.start,
                valmax=slider_data.end,
                valinit=slider_data.init,
                valstep=slider_data.step,
            )
            self._sliders_data[slider_data.name] = slider
            slider.on_changed(self._update)
        self._update()
        plt.show()

    def _update(self, _ = None):
        values = {name: slider.val for name, slider in self._sliders_data.items()}
        self.update(values)

    def update(self, values: dict):
        pass
