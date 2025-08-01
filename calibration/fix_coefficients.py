import paths
import pandas as pd


from processing.MERSIImage import MERSIImage

def fix_coeffs(image: MERSIImage):
    coeffs = pd.read_csv(paths.COEFFS_DIR / "coeff_correction.csv")
    coeffs = coeffs.set_index("band")

    band = int(image.band)
    # slope, intercept = coeffs.loc[band]
    # cal0, cal1, cal2 = image.vis_cal[band - 1]
    # cal1 = cal1 * slope
    # cal0 = cal0 * slope + intercept
    # image.vis_cal[band - 1] = (cal0, cal1, cal2)
    new_cal0 = coeffs.loc[band, "new_cal0"]
    new_cal1 = coeffs.loc[band, "new_cal1"]
    image.vis_cal[band - 1, 0] = new_cal0
    image.vis_cal[band - 1, 1] = new_cal1