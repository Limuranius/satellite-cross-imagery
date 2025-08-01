import datetime

import numpy as np
import matplotlib.pyplot as plt
import tqdm
from netCDF4 import Dataset

import paths
from web import NASA_parser


class MODISChlor:
    def __init__(self, path: str):
        ds = Dataset(path, "r")
        self.chl = ds.variables["chlor_a"]
        self.lat = np.array(ds.variables["lat"])
        self.lon = np.array(ds.variables["lon"])

    def get_point(self, lon: float, lat: float):
        lon_i = np.abs(self.lon - lon).argmin()
        lat_i = np.abs(self.lat - lat).argmin()
        return self.chl[lat_i, lon_i]

    def get_map(
            self,
            lons: np.ndarray,  # 2d array
            lats: np.ndarray,  # 2d array
    ):
        h, w = lons.shape
        chl = np.zeros_like(lons)
        for i in tqdm.trange(h, position=0):
            for j in range(w):
                chl[i, j] = self.get_point(lon=lons[i, j], lat=lats[i, j])
        # lon_i = np.abs(lons[:, :, None] - self.lon).argmin(axis=-1)
        # lat_i = np.abs(lats[:, :, None] - self.lat).argmin(axis=-1)
        # print(lon_i.shape)
        # print(lat_i.shape)
        # return self.chl[lon_i, lat_i]
        return chl

    def show(self):
        plt.imshow(self.chl)
        plt.show()

    @classmethod
    def from_dt(cls, dt: datetime.datetime):
        filename = dt.strftime("AQUA_MODIS.%Y%m%d.L3m.DAY.CHL.chlor_a.4km.nc")
        path = paths.MODIS_CHLOROPHYL_DIR / filename
        if path.exists():
            return MODISChlor(path)
        else:
            NASA_parser.download_chlor_a(dt)

