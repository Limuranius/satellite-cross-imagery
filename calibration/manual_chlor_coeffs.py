import pickle

import matplotlib.pyplot as plt
import numpy as np

import paths
import utils
from processing import algorithms
from processing.MERSIImage import MERSIImage
from processing.MODISChlor import MODISChlor
from visuals.graphs import InteractivePlot

sliders = []
coeffs = (0.2424, -2.7423, 1.8017, 0.0015, -1.228)
interv = 1.0
for i in range(5):
    c = coeffs[i]
    # start = c - c * interv
    # end = c + c * interv

    start = c - 1
    end = c + 1
    start, end = min(start, end), max(start, end)
    sliders.append(InteractivePlot.SliderData(name=str(i), start=start, end=end, init=c, step=None))

df = pickle.load(open(paths.DATA_DIR / "data_with_mersi_preproc.pickle", "rb"))
# df = pickle.load(open(paths.DATA_DIR / "data_with_mersi_preproc_aeronet_calib.pickle", "rb"))

# mask = df["aeronet_AERONET_Site_Name"] == "ARIAKE_TOWER"
# mask &= df["mersi_senz"] <= 10
# row = df[mask].iloc[0]
# img = MERSIImage.from_dt(row["mersi_t"], "8")
# i, j = img.get_closest_pixel(lon=row["aeronet_lon"], lat=row["aeronet_lat"])
# j += 200
# i -= 100
# size = 300
# area_slice = [
#     slice(max(0, i - size // 2), i + size // 2),
#     slice(max(0, j - size // 2), j + size // 2),
# ]
# chl = MODISChlor.from_dt(img.dt)
# chl = chl.get_map(
#     lons=img.longitude[*area_slice],
#     lats=img.latitude[*area_slice],
# )
# _, rrs = pickle.load(open(r"C:\Users\Gleb\PycharmProjects\satellite-cross-imagery\notebooks\chl_6s_4.npy", "rb"))


class Plot(InteractivePlot):
    sliders = sliders

    def update(self, values: dict):
        coeffs = list(values.values())
        print(coeffs)

        rrs = [
            df["mersi_6S_atmos_corrected_reflectance_brdf[443nm]"],
            df["mersi_6S_atmos_corrected_reflectance_brdf[490nm]"],
            df["mersi_6S_atmos_corrected_reflectance_brdf[555nm]"],
        ]
        # global rrs
        # rrs = rrs.transpose(2, 0, 1)

        new_chl = algorithms.chl_oc3(rrs, coeffs=coeffs)
        # df["new_mersi_chl"] = new_chl

        # x = df["aeronet_chlor_a_from_rrs"].values
        # y = df["new_mersi_chl"].values

        x = new_chl.values
        # y = df["nir_chlor_a_mean"].values
        y = df["aeronet_chlor_a_from_rrs"].values

        # x = new_chl.flatten()
        # y = chl.flatten()

        m = ~np.isnan(x) & ~np.isnan(y)
        x = x[m]
        y = y[m]
        m = utils.filter_two_sigma_mask(x - y)
        x = x[m]
        y = y[m]
        a = min(x.min(), y.min())
        b = max(x.max(), y.max())
        self.scatter.set_offsets(np.column_stack((x, y)))

        self.line.set_xdata([a, b])
        self.line.set_ydata([a, b])
        self.fig.canvas.draw_idle()


plt.xlim(0, 30)
plt.ylim(0, 30)
Plot()
