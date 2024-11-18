import numpy as np
import calibration.utils
import matplotlib.pyplot as plt
from scipy.optimize import minimize


class Band12Optimizer:
    original_values: list[np.ndarray]
    true_values: list[np.ndarray]
    true_noise: list[np.ndarray]

    def __init__(self, areas: list[np.ndarray], max_water_factor: float):
        self.original_values = areas
        self.true_values = [
            calibration.utils.calculate_true_values(area, max_water_factor)
            for area in areas
        ]
        self.true_noise = [orig - true for orig, true in zip(self.original_values, self.true_values)]

    def show(self):
        _, ax = plt.subplots(nrows=3, sharex=True, sharey=True)
        ax[0].imshow(np.concatenate(self.original_values))
        ax[1].imshow(np.concatenate(self.true_values))
        ax[2].imshow(np.concatenate(self.true_noise))
        plt.show()

    def calculate_coeffs(self, sensor: int) -> tuple[int, float]:
        MIN_WIN_SIZE = 1
        MAX_WIN_SIZE = 10

        optimal_win_size = None
        optimal_coeffs = None
        min_error = float("inf")
        for win_size in range(MIN_WIN_SIZE, MAX_WIN_SIZE + 1):
            coeffs = np.zeros(1)
            res = minimize(
                fun=self.__error_function,
                x0=coeffs,
                args=(sensor, win_size),
            )
            coeffs = res.x
            if res.fun < min_error:
                optimal_win_size = win_size
                optimal_coeffs = coeffs
                min_error = res.fun
        return optimal_win_size, float(optimal_coeffs)

    def __error_function(self, coeffs: np.ndarray, sensor: int, win_size: int) -> float:
        predicted_noise = np.concatenate(self.__predict_sensor_noise(coeffs, sensor, win_size))
        error = np.concatenate(self.true_noise, axis=1)[sensor] - predicted_noise
        error_sq = error ** 2
        return error_sq.sum()

    def __predict_sensor_noise(self, coeffs: np.ndarray, sensor: int, win_size: int) -> list[np.ndarray]:
        results = []
        a = coeffs[0]
        for area in self.original_values:
            sensor_values = area[sensor]
            avg_values = right_avg_convolve(sensor_values, win_size)
            diff = avg_values - sensor_values
            diff_coeff = a * diff
            results.append(diff_coeff)
        return results


def right_avg_convolve(arr: np.ndarray, win_size: int):
    result = np.empty_like(arr)
    for i in range(len(arr)):
        result[i] = arr[i: i + win_size + 1].mean()
    return result
