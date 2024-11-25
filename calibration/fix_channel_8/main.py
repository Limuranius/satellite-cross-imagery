from datetime import datetime

import calibration.manually_draw_edges
from processing.MERSIImage import MERSIImage
import calculate_coeffs

COLOR = (0, 0, 255)  # BGR
IMAGERY_DTS = [
    "2024-01-12 13:50:00",
    "2024-01-17 15:40:00",
    "2024-01-22 17:30:00",
    "2024-01-30 06:35:00",
    "2024-02-04 08:20:00",
    "2024-02-06 21:15:00",
    "2024-02-09 10:10:00",
    "2024-02-14 12:00:00",
    "2024-02-29 15:45:00",
    "2024-04-15 02:00:00",
    "2024-04-30 04:15:00",
    "2024-05-02 17:00:00",
    "2024-05-12 17:15:00",
    "2024-05-15 06:10:00",
    "2024-06-06 19:35:00",
    "2024-10-01 20:00:00",
]
IMAGERY_DTS = [datetime.fromisoformat(dt_str) for dt_str in IMAGERY_DTS]

# Collecting all areas with edges from imagery
areas = []
for dt in IMAGERY_DTS:
    image = MERSIImage.from_dt(dt, "8")
    image_areas = calibration.manually_draw_edges.image_to_edge_areas(
        image.counts,
        edge_mask=calibration.manually_draw_edges.load_edge_mask(dt, mask_pixels_color_bgr=COLOR),
    )
    areas += image_areas

# Calculating coefficients for band 8 sensor zero
opt = calculate_coeffs.Band8Optimizer(
    areas,
    max_water_factor=1.3,
)
opt.show()
coeffs = opt.calculate_coeffs(0)
print(coeffs)