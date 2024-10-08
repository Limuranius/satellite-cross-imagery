import numpy as np
import satpy

import paths
from .SatelliteImage import SatelliteImage
import os


class MERSIImage(SatelliteImage):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.scene = satpy.Scene(
            [file_path] + os.listdir(paths.MERSI_L1_GEO_DIR),
            "mersi2_l1b"
        )
        self.scene.load(["latitude", "longitude"])
        self.scene.load(["8"], "radiance")

    def latitude(self) -> np.ndarray[float, float]:
        return self.scene["latitude"].to_numpy()

    def longitude(self) -> np.ndarray[float, float]:
        return self.scene["longitude"].to_numpy()

    def radiance(self) -> np.ndarray[float, float]:
        return self.scene["8"].to_numpy()
