import numpy as np
from scipy.stats import linregress, gaussian_kde


def relplot_with_linregress(
        x, y, ax
):
    # Calculate the point density
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)

    lin = linregress(x, y)
    ax.scatter(x, y, c=z, s=1)
    ax.plot(x, x * lin.slope + lin.intercept, "--")
    txt = f"""{lin.slope=:.5f}
    {lin.intercept=:.5f}
    {lin.rvalue**2=:.5f}
    """
    ax.text(
        0,
        1,
        txt,
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes,
    )