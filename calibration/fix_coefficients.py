import paths
import pandas as pd

from processing.MERSIImage import MERSIImage

coeffs = pd.read_csv(paths.COEFFS_DIR / "coeff_correction.csv")
coeffs = coeffs.set_index("band")


def fix_coeffs(image: MERSIImage):
    band = int(image.band)
    slope, intercept = coeffs.loc[band]
    cal0, cal1, cal2 = image.vis_cal[band - 1]
    cal1 = cal1 * slope
    cal0 = cal0 * slope + intercept
    image.vis_cal[band - 1] = (cal0, cal1, cal2)
