import os

import numpy as np
import tqdm
import csv
import paths
from processing.MERSIImage import MERSIImage


def load_coeffs() -> np.ndarray:
    """
    float[15, 10, 2] - band, sensor, (slope, intercept)
    """
    path = os.path.join(paths.COEFFS_DIR, "zebra_coeffs.csv")
    # path = os.path.join(paths.COEFFS_DIR, "zebra_coeffs_ice.csv")
    with open(path, newline="") as file:
        reader = csv.reader(file)
        next(reader)  # skipping header
        coeffs = [list() for _ in range(15)]
        for band_i in range(15):  # each band
            for _ in range(10):  # each sensor
                row = next(reader)
                band, sensor, slope, intercept = row[0], row[1], float(row[2]), float(row[3])
                coeffs[band_i].append((slope, intercept))
    return np.array(coeffs)


def apply_coeffs(image: np.ndarray, coeffs: np.ndarray):
    """
    image - int[2000, 2048]
    coeffs - float[10, 2] - sensor, (slope, intercept)
    """
    height = image.shape[0]
    new_image = image.copy()
    pbar = tqdm.tqdm(desc="Calibrating zebra", total=2000, unit="rows")
    for sensor in range(10):
        slope, intercept = coeffs[sensor]
        for y in range(sensor, height, 10):
            row = image[y]
            predicted_noise = row * slope + intercept
            new_image[y] -= predicted_noise.astype(int)
            pbar.update(1)
    pbar.close()
    return new_image


def correct_mersi_image(image: MERSIImage) -> None:
    coeffs = load_coeffs()
    band_i = int(image.band) - 5
    band_coeffs = coeffs[band_i]
    image.counts = apply_coeffs(image.counts, band_coeffs)


