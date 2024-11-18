import calibration.manually_draw_edges
from processing.MERSIImage import MERSIImage
import calculate_coeffs

IMAGERY_DTS = []

# Collecting all areas with edges from imagery
areas = []
for dt in IMAGERY_DTS:
    image = MERSIImage.from_dt(dt)
    image_areas = calibration.manually_draw_edges.image_to_edge_areas(
        image,
        edge_mask=calibration.manually_draw_edges.load_edge_mask(dt),
    )
    areas += image_areas

# Calculating coefficients for band 8 sensor zero
opt = calculate_coeffs.Band8Optimizer(
    areas,
    max_water_factor=0.3,
)
coeffs = opt.calculate_coeffs(0)
print(coeffs)