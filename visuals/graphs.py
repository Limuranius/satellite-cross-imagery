import os
import pathlib

import pandas as pd
from sklearn.linear_model import LinearRegression

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress, gaussian_kde


def relplot_with_linregress(
        x: pd.Series, y, ax, s=1, fit_intercept=True,
):
    # Calculate the point density
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    ax.scatter(x, y, c=z, s=s)

    lin = LinearRegression(fit_intercept=fit_intercept)
    lin.fit(x.to_frame(), y)

    slope = lin.coef_[0]
    intercept = lin.intercept_

    if fit_intercept:
        txt = f"""slope={slope:.5f}
intercept={intercept:.5f}
r^2={lin.score(x.to_frame(), y):.5f}
"""
    else:
        txt = f"""slope={slope:.5f}
r^2={lin.score(x.to_frame(), y):.5f}
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
