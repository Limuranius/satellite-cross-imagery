import numpy as np

coeff_12_neighbor = np.array([0.005525776215582893, 0.005555067369654363, 0.005555067369654363, 0.0054964850615114216, 0.005437902753368482, 0.008894258933801991, 0.0029481546572934967, 0.003680433509080257, 0.004149091974223784, 0.004149091974223784])
coeff_8_neighbor = np.array([0.03077328646748681, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])


COEFFS = {
    "8": {
        "left_window": 1,
        "right_window": 1,
        "neighbor_influence": np.repeat(coeff_8_neighbor[:, None], 10, axis=1),
        "trace": np.zeros(10),
    },
    "12": {
        "left_window": 1,
        "right_window": 3,
        "neighbor_influence": np.repeat(coeff_12_neighbor[:, None], 10, axis=1),
        "trace": np.array([0.03904511, 0.05486233, 0.0794669, 0.11110135, 0.13687756, 0.15210896
            , 0.13101933, 0.09352665, 0.05896309, 0.0413884])
    },
    "13": {
        "left_window": 1,
        "right_window": 5,
        "neighbor_influence": np.full((10, 10), 0.0065),
        "trace": np.zeros(10),
    },
    "15": {
        "left_window": 1,
        "right_window": 1,
        "neighbor_influence": np.zeros((10, 10)),
        "trace": np.zeros(10),
    }
}
