import paths
import pandas as pd

from processing.MERSIImage import MERSIImage

coeffs = pd.read_csv(paths.COEFFS_DIR / "coeff_intercept.csv")
coeffs = coeffs.set_index("band")


def fix_intercept(image: MERSIImage):
    band = int(image.band)
    new_coeff = coeffs.loc[band, "new_coeff"]
    image.vis_cal[band - 1, 0] = new_coeff
