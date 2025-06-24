import os
import pathlib

import pandas as pd
from sklearn.linear_model import LinearRegression

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress, gaussian_kde


def relplot_with_linregress(
        x: pd.Series | np.ndarray,
        y: pd.Series | np.ndarray,
        ax=None,
        s=1,
        fit_intercept=True,
        sample_size=10000,
):
    if ax is None:
        ax = plt.subplot()
    data = pd.DataFrame({"x": x, "y": y})

    # Calculating linear regression
    lin = LinearRegression(fit_intercept=fit_intercept)
    lin.fit(data[["x"]], data["y"])
    slope = lin.coef_[0]
    intercept = lin.intercept_
    r2 = lin.score(data[["x"]], data["y"])

    # Calculate the point density
    data = data.sample(n=min(len(data), sample_size), random_state=42)  # Sampling data, so it fits on plot
    x = data["x"]
    y = data["y"]
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    ax.scatter(x, y, c=z, s=s)

    if fit_intercept:
        txt = f"""slope={slope:.5f}
intercept={intercept:.5f}
r^2={r2:.5f}
"""
    else:
        txt = f"""slope={slope:.5f}
r^2={r2:.5f}
"""

    ax.plot(x, x * slope + intercept, "--")

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
