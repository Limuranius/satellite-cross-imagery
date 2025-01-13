from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
import processing.matching


MATCHING_PIXELS_KWARGS = dict(
    max_zenith_relative_diff=0.05,
    max_zenith=3000,
    exclude_clouds=False,
    exclude_land=False,
    exclude_water=False,
    do_erosion=False,
    correct_cloud_movement=False,
    use_rstd_filtering=True,
    rstd_kernel_size=5,
    rstd_threshold=0.05,
    exclude_overflow=True,
)


class MatchingImageryPair:
    img_mersi: MERSIImage
    img_modis: MODISImage

    def __init__(self, mersi: MERSIImage, modis: MODISImage):
        self.img_mersi = mersi
        self.img_modis = modis

    def load_matching_pixels(self):
        return processing.matching.load_matching_pixels(
            self.img_mersi,
            self.img_modis,
            **MATCHING_PIXELS_KWARGS,
        )

    def matching_stats(self):
        return processing.matching.matching_stats(
            self.img_mersi,
            self.img_modis,
            self.load_matching_pixels(),
        )

    def aggregated_matching_stats(self, kernel_size: int = 5):
        return processing.matching.aggregated_matching_stats(
            self.img_mersi,
            self.img_modis,
            self.load_matching_pixels(),
            kernel_size,
        )

    def visualize_matching_pixels(self):
        processing.matching.visualize_matching_pixels(
            self.img_mersi,
            self.img_modis,
            self.load_matching_pixels(),
        )