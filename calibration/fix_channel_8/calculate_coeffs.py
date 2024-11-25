import numpy as np
import calibration.utils
import matplotlib.pyplot as plt
from scipy.optimize import minimize


class Band8Optimizer:
    original_values: np.ndarray
    true_values: np.ndarray
    true_noise: np.ndarray

    def __init__(self, areas: list[np.ndarray], max_water_factor: float):
        self.original_values = np.concatenate(areas, axis=1)
        self.true_values = np.concatenate([
            calibration.utils.calculate_true_values(area, max_water_factor)
            for area in areas
        ], axis=1)
        self.true_noise = self.original_values - self.true_values

    def show(self):
        _, ax = plt.subplots(nrows=3, sharex=True, sharey=True)
        ax[0].imshow(self.original_values)
        ax[1].imshow(self.true_values)
        ax[2].imshow(self.true_noise)
        plt.show()

    def calculate_coeffs(self, sensor: int):
        coeffs = np.zeros(10)
        res = minimize(
            fun=self.__error_function,
            x0=coeffs,
            args=(sensor,),
        )
        print(res)
        coeffs = res.x
        return coeffs

    def __error_function(self, coeffs: np.ndarray, sensor: int) -> float:
        sensor_predicted_noise = self.__predict_sensor_noise(coeffs, sensor)
        error = self.true_noise[sensor] - sensor_predicted_noise
        error_sq = error ** 2
        return error_sq.sum()

    def __predict_sensor_noise(self, coeffs: np.ndarray, sensor: int):
        sens_diff = self.original_values - self.original_values[sensor]
        sens_diff_coeff = sens_diff * coeffs.reshape(10, 1)
        predicted_noise = sens_diff_coeff.sum(axis=0)
        return predicted_noise
