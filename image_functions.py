import numpy as np


def get_closest_coords_pixel(
        lon: float,
        lat: float,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
):
    distance = (
            np.abs(lat_grid - lat) ** 2
            + np.abs(lon_grid - lon) ** 2
    )
    i, j = np.unravel_index(distance.argmin(), distance.shape)
    return i, j
