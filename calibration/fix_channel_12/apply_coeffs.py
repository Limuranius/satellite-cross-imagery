import numpy as np
import tqdm

from .calculate_coeffs import right_avg_convolve


def load_coeffs() -> np.ndarray:
    path = "/home/gleb123/satellite-cross-imagery/calibration/fix_channel_12/coeff_table_12.txt"
    coeffs = []
    with open(path) as file:
        for line in file:
            coeffs.append(list(map(float, line.split())))
    return np.array(coeffs)


def apply_coeffs(image: np.ndarray, coeffs: np.ndarray):
    """
    image - int[2000, 2048]
    coeffs - array[int[10], float[10], float[10]]
    """
    height = image.shape[0]
    new_image = image.copy()
    pbar = tqdm.tqdm(desc="Calibrating band 12 image", total=2000, unit="rows")
    for sensor in range(10):
        win_size, a, b = coeffs[sensor]
        win_size = int(win_size)
        for y in range(sensor, height, 10):
            row = image[y]
            row_mean = right_avg_convolve(row, win_size)
            diff = row_mean - row
            predicted_noise = a * diff + b * diff ** 2
            new_image[y] -= predicted_noise.astype(int)
            pbar.update(1)
    pbar.close()
    return new_image
