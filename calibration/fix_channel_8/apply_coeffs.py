import numpy as np


def load_coeffs() -> np.ndarray:
    path = "/home/gleb123/satellite-cross-imagery/calibration/fix_channel_8/coeff_table_8.txt"
    coeffs = []
    with open(path) as file:
        for line in file:
            coeffs.append(list(map(float, line.split())))
    return np.array(coeffs)


def apply_coeffs(image: np.ndarray, coeffs: np.ndarray):
    """
    image - int16[2000, 2048]
    coeffs - float[10, 10]
    """
    height = image.shape[0]
    new_image = image.copy()
    for sensor in range(10):
        sensor_coeffs = coeffs[sensor]
        for y in range(sensor, height, 10):
            scan_line = image[y // 10 * 10: (y // 10 + 1) * 10, :]
            sens_diff = scan_line - scan_line[sensor]
            sens_diff_coeff = sens_diff * sensor_coeffs.reshape(10, 1)
            predicted_noise = sens_diff_coeff.sum(axis=0)
            new_image[y] -= predicted_noise.astype(int)
    return new_image
