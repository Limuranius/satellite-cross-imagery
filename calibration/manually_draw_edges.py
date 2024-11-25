from datetime import datetime
import os
import cv2
import numpy as np

import paths
from processing.MERSIImage import MERSIImage


def load_edge_mask(dt: datetime, band: str):
    fmt = f"%Y%m%d %H%M band{band}.png"
    file_path = os.path.join(paths.EDGE_MASKS_DIR, dt.strftime(fmt))
    if not os.path.exists(file_path):
        img = MERSIImage.from_dt(dt, band).counts

        # Changing contrast
        vmin, vmax = {
            "8": (500, 1500),
            "12": (350, 800),
        }[band]
        img[img < vmin] = vmin
        img[img > vmax] = vmax
        img -= vmin
        img = img / (vmax - vmin) * 4095

        img = (img // 16).astype(np.uint8)

        cv2.imwrite(file_path, img)
        input(f"Draw edges with RGB(255, 0, 0) on {file_path}, save and press Enter")
    mask = cv2.imread(file_path)
    mask = mask == (0, 0, 255)
    return np.all(mask, axis=2)


def mask2d_to_coordinates(mask: np.ndarray) -> np.ndarray:
    indices = np.arange(mask.shape[0] * mask.shape[1]).reshape(mask.shape)
    coords = np.array(np.unravel_index(indices, mask.shape)).transpose(1, 2, 0)
    return coords[mask]


def image_to_edge_areas(
        image: np.ndarray,
        edge_mask: np.ndarray,
        left_width: int = 20,
        right_width: int = 20,
) -> list[np.ndarray]:
    result = []
    pixels = mask2d_to_coordinates(edge_mask)
    visited = np.zeros_like(edge_mask, dtype=bool)
    for (y, x) in pixels:
        if not visited[y, x]:
            y_start = y // 10 * 10
            y_end = (y // 10 + 1) * 10
            x_start = max(0, x - left_width)
            x_end = min(image.shape[1], x + right_width)
            # print(y_start, y_end, x_start, x_end)
            result.append(image[y_start: y_end, x_start: x_end])
            visited[y_start: y_end, x_start: x_end] = True
    return result

