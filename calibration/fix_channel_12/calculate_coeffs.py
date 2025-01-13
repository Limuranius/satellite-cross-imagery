import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

import calibration.utils


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
        i = -1
        for orig, true, noise in zip(self.original_values, self.true_values, self.true_noise):
            _, ax = plt.subplots(nrows=3, sharex=True, sharey=True)
            ax[0].imshow(orig)
            ax[1].imshow(true)
            ax[2].imshow(noise)
            plt.title(str(i := i + 1))
            plt.show()

    def noise_diff_relation(self, sensor: int, window_size: int, areas_indices: list[int] = None):
        if areas_indices is None:
            areas_indices = range(len(self.original_values))
        diffs = []
        noises = []
        for i in areas_indices:
            orig = self.original_values[i]
            noise = self.true_noise[i]
            orig = orig[sensor]
            noise = noise[sensor]
            # means = right_avg_convolve(orig, window_size)
            # diff = means - orig
            diff = diff_right_window(orig, window_size)
            diffs += list(diff[noise > 0])
            noises += list(noise[noise > 0])
        plt.scatter(diffs, noises)

        plt.title(f"Канал 12, датчик {sensor}, ширина окна {window_size}")
        plt.xlabel("Разница в яркости")
        plt.ylabel("Остаточный сигнал")
        # plt.show()

    def calculate_coeffs(self, sensor: int, min_win_size: int, max_win_size: int) -> tuple[int, np.ndarray]:
        optimal_win_size = None
        optimal_coeffs = None
        min_error = float("inf")
        for win_size in range(min_win_size, max_win_size + 1):
            coeffs = np.zeros(2)
            res = minimize(
                fun=self.__error_function,
                x0=coeffs,
                args=(win_size, sensor),
            )
            coeffs = res.x
            if res.fun < min_error:
                optimal_win_size = win_size
                optimal_coeffs = coeffs
                min_error = res.fun
        return optimal_win_size, optimal_coeffs

    def __error_function(self, coeffs: np.ndarray, win_size: int, sensor: int) -> float:
        predicted_noise = np.concatenate(self.__predict_sensor_noise(coeffs, win_size, sensor))
        error = np.concatenate(self.true_noise, axis=1)[sensor] - predicted_noise
        error_sq = error ** 2
        return error_sq.sum()

    def __predict_sensor_noise(self, coeffs: np.ndarray, win_size: int, sensor: int) -> list[np.ndarray]:
        results = []
        a, b = coeffs
        for area in self.original_values:
            sensor_values = area[sensor]
            # avg_values = right_avg_convolve(sensor_values, win_size)
            # diff = avg_values - sensor_values
            diff = diff_right_window(sensor_values, win_size)
            diff_coeff = a * diff + b * diff ** 2
            results.append(diff_coeff)
        return results


def right_avg_convolve(arr: np.ndarray, win_size: int):
    result = np.empty_like(arr)
    for i in range(len(arr)):
        result[i] = arr[i: i + win_size + 1].mean()
    return result


def right_avg_weighted_convolve(arr: np.ndarray, win_size: int):
    result = np.empty_like(arr)
    for i in range(len(arr)):
        window = arr[i: i + win_size + 1]
        weights = np.ones_like(window) / np.arange(1, len(window) + 1)
        result[i] = (window * weights).mean()
    return result

def diff_right_window(arr: np.ndarray, win_size: int):
    result = np.empty_like(arr)
    for i in range(len(arr)):
        window = arr[i: i + win_size + 1]
        diff = window - arr[i]
        weights = np.ones_like(window) / np.arange(1, len(window) + 1)
        result[i] = (diff * weights).mean()
    return result