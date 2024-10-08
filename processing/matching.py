from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from global_land_mask import globe


def get_matching_pixels(
        image_mersi: MERSIImage,
        image_modis: MODISImage,
        max_zenith_diff: int
) -> list[tuple[int, int], tuple[int, int]]:
    result = []
    for i in range(2000):  # MERSI height
        for j in range(2048):  # MERSI width

            lon = image_mersi.longitude()[i, j]
            lat = image_mersi.latitude()[i, j]

            # Skip pixels that don't contain water
            if globe.is_land(lat, lon):
                continue

            # Find matching pixel in other image
            if not image_modis.contains_pos(lat, lon):
                continue
            modis_i, modis_j = image_modis.get_closest_pixel(lon, lat)

            # Check zenith difference
            zenith_mersi = image_mersi.sensor_zenith()[i, j]
            zenith_modis = image_modis.sensor_zenith()[modis_i, modis_j]
            if abs(zenith_modis - zenith_mersi) > max_zenith_diff:
                continue

            result.append(((i, j), (modis_i, modis_j)))
    return result
