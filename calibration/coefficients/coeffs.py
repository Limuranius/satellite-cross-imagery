import numpy as np

coeff_12_neighbor = np.array([0.005525776215582893, 0.005555067369654363, 0.005555067369654363, 0.0054964850615114216, 0.005437902753368482, 0.008894258933801991, 0.0029481546572934967, 0.003680433509080257, 0.004149091974223784, 0.004149091974223784])
coeff_8_neighbor = np.array([0.03077328646748681, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

ZERO_COEFFS = {
    "left_window": 1,
    "right_window": 1,
    "neighbor_influence": np.zeros((10, 10)),
    "trace": np.zeros(10),
    "mean_window": {"coeffs": [0.0] * 10, "left_window": 0, "right_window": 0}
}

COEFFS = {
    "8": {
        "left_window": 1,
        "right_window": 1,
        "neighbor_influence": np.repeat(coeff_8_neighbor[:, None], 10, axis=1),
        "trace": np.zeros(10),

        "mean_window": {
            "coeffs": [0.0] * 10,
            "left_window": 0,
            "right_window": 0,
        }
    },
    "9": ZERO_COEFFS,
    "10": ZERO_COEFFS,
    "11": ZERO_COEFFS,
    "12": {
        "left_window": 1,
        "right_window": 3,
        # "neighbor_influence": np.repeat(coeff_12_neighbor[:, None], 10, axis=1),
        "neighbor_influence": np.zeros((10, 10)),
        "trace": np.array([0.026157000585823084, 0.041974223784417106, 0.06423550087873463, 0.08825424721734036, 0.10289982425307558, 0.12281780902167545, 0.09821323960164031, 0.077709431751611, 0.05369068541300527, 0.03260105448154657]),

        # "mean_window": {
        #     "coeffs": [0.03] * 10,
        #     "left_window": 7,
        #     "right_window": 7,
        # },

        "mean_window": {
            "coeffs": [0.025] * 10,
            "left_window": 8,
            "right_window": 6,
        }
    },
    "13": {
        "left_window": 1,
        "right_window": 5,
        # "neighbor_influence": np.full((10, 10), 0.0065),
        "neighbor_influence": np.zeros((10, 10)),
        "trace": np.zeros(10),

        "mean_window": {
            "coeffs": [0.0183] * 10,
            "left_window": 0,
            "right_window": 12,
        },
    },
    "14": ZERO_COEFFS,
    "15": {
        "left_window": 1,
        "right_window": 1,
        "neighbor_influence": np.zeros((10, 10)),
        "trace": np.zeros(10),

        "mean_window": {
            "coeffs": [0.0] * 10,
            "left_window": 0,
            "right_window": 0,
        },

        "band15_coeffs": {
            "up": 15,
            "down": 15,
            "left": 15,
            "right": 15,
            "coeffs": np.array([
                0.8,
                0, 0, 0, 0, 0, 0, 0, 0,
                1.35,
            ])
        }
    }
}

