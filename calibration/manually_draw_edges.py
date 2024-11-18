from datetime import datetime
import os
import cv2
import numpy as np

from processing.MERSIImage import MERSIImage


def load_edge_mask(dt: datetime):
    fmt = "%Y%m%d %H%M.jpg"
    file_path = os.path.join("edges masks", dt.strftime(fmt))
    if not os.path.exists(file_path):
        img = MERSIImage.from_dt(dt).colored_image()
        cv2.imwrite(file_path, img)
        input(f"Draw edges with red color on {file_path}, save and press Enter")
    mask = cv2.imread(file_path)
    mask = mask == (0, 0, 255)
    return mask


def mask2d_to_coordinates(mask: np.ndarray):
    indices = np.arange(mask.shape[0] * mask.shape[1]).reshape(mask.shape)
    coords = np.array(np.unravel_index(indices, mask.shape)).transpose(1, 2, 0)
    return coords[mask]


def image_to_edge_areas(
        image: np.ndarray,
        edge_mask: np.ndarray,
        area_width: int = 100
) -> list[np.ndarray]:
    result = []
    pixels = mask2d_to_coordinates(edge_mask)
    visited = np.zeros_like(edge_mask, dtype=bool)
    for (y, x) in pixels:
        if not visited[y, x]:
            y_start = y // 10 * 10
            y_end = (y // 10 + 1) * 10
            x_start = max(0, x - area_width // 2)
            x_end = min(image.shape[1], x + area_width // 2)
            result.append(image[y_start: y_end, x_start: x_end])
            visited[y_start: y_end, x_start: x_end] = True
    return result

