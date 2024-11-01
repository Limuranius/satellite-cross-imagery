import os

import numpy as np
from tqdm import tqdm

import paths
from processing.SatelliteImage import SatelliteImage


def get_rstd_map_path(img: SatelliteImage, kernel_size: int):
    date_str = img.dt.strftime("%Y%m%d%H%M")
    file_name = f"{img.satellite_name} {date_str} band{img.band} kernel{kernel_size}.npy"
    return os.path.join(
        paths.RSTD_MAPS_DIR,
        file_name
    )

def calculate_rstd_map(arr: np.ndarray, kernel_size: int):
    radius = kernel_size // 2
    h, w = arr.shape
    out = np.empty_like(arr, dtype=np.float16)
    with tqdm(total=h * w, desc="Std sum map: ") as pbar:
        for x in range(w):
            for y in range(h):
                area = arr[y - radius: y + radius + 1, x - radius: x + radius + 1]
                out[y, x] = area.std() / area.mean()
                pbar.update(1)
    return out

def load_rstd_map(img: SatelliteImage, kernel_size: int) -> np.ndarray:
    file_path = get_rstd_map_path(img, kernel_size)
    if os.path.exists(file_path):
        return np.load(file_path)
    else:
        rstd_map = calculate_rstd_map(img.radiance, kernel_size)
        np.save(file_path, rstd_map)
        return rstd_map
