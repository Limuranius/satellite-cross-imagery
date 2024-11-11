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
    txt = f"""slope={lin.slope:.5f}
intercept={lin.intercept:.5f}
r^2={lin.rvalue**2:.5f}
    """
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