import datetime

import numpy as np
import matplotlib.pyplot as plt
import tqdm
from netCDF4 import Dataset
from pykdtree.kdtree import KDTree

import paths
from web import NASA_parser


class MODISChlor:
    def __init__(self, path: str):
        ds = Dataset(path, "r")
        self.chl = np.array(ds.variables["chlor_a"][:])
        self.chl[self.chl < 0] = np.nan
        self.lat = np.array(ds.variables["lat"])
        self.lon = np.array(ds.variables["lon"])

        lon2d, lat2d = np.meshgrid(self.lon, self.lat)
        coords = np.array([lon2d, lat2d])
        coords = coords.transpose((1, 2, 0))
        coords = coords.reshape((-1, 2))  # flatten
        self.tree = KDTree(coords)

    def get_point(self, lon: float, lat: float):
        lon_i = np.abs(self.lon - lon).argmin()
        lat_i = np.abs(self.lat - lat).argmin()
        return self.chl[lat_i, lon_i]

    def get_map(
            self,
            lons: np.ndarray,  # 2d array
            lats: np.ndarray,  # 2d array
    ):
        coords = np.array([lons, lats])
        coords = coords.transpose((1, 2, 0))
        coords = coords.reshape((-1, 2))  # flatten
        distance, indices = self.tree.query(coords)
        i, j = np.unravel_index(indices, self.chl.shape)
        return self.chl[i, j].reshape(lons.shape)

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

