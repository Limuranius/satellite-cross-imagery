import numpy as np


def find_mean_water_brightness(area: np.ndarray) -> float:
    hist_y, hist_x = np.histogram(area[area < 2000], bins=50)
    return float((hist_x[hist_y.argmax()] + hist_x[hist_y.argmax() + 1]) / 2)


def calculate_water_mask(
        area: np.ndarray,
        max_water_factor: float) -> np.ndarray:
    water_avg_value = find_mean_water_brightness(area)
    max_water_value = water_avg_value * max_water_factor
    return area <= max_water_value


def calculate_true_values(
        area: np.ndarray,
        max_water_factor: float
) -> np.ndarray:
    water_mask = calculate_water_mask(area, max_water_factor)
    water_value = find_mean_water_brightness(area)
    true_values_area = area.copy()
    true_values_area[water_mask] = water_value
    return true_values_area
