import collections
import datetime
import pickle

import numpy as np
import pandas as pd
import tqdm
from processing.algorithms import atmosphere_correction

import paths
from processing.MERSIImage import MERSIImage, MERSI_BANDS_WAVELEN
from processing.MODISImage import MODIS_BANDS_WAVELEN, MODISImage
import SRF.mersi_2_srf
import SRF.modis_aqua_srf


import processing
processing.MODISImage.LAZY_MODE = True
processing.MERSIImage.LAZY_MODE = True


def outliers_thresholds(data: np.ndarray) -> tuple[float, float]:
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    threshold = 1.5 * iqr
    return (q1 - threshold), (q3 + threshold)


def outliers_mask(data):
    l, r = outliers_thresholds(data)
    return (data < l) | (data > r)


def outliers_2d_mask(data_2d: np.ndarray):
    data = data_2d.flatten()
    mask_1d = outliers_mask(data)
    return mask_1d.reshape(data_2d.shape)


def homogeneous_pixels_mask(image: MERSIImage, area_idx):
    band13 = image.get_band("13")
    reflectance13 = band13.reflectance[*area_idx]
    mask = reflectance13 < 0.1  # Альбедо 10% всегда облачность
    if mask.sum() == 0:
        return None
    l, r = outliers_thresholds(reflectance13[mask])
    mask = mask & (reflectance13 >= l) & (reflectance13 <= r)
    return mask


class TablePrecompute:
    df: pd.DataFrame

    def __init__(self, df):
        self.df = df

    def iterate_rows_timedelta_within_image(self, image: MERSIImage):
        timedelta = (self.df["aeronet_t"] - image.dt).abs()
        good_timedelta = self.df[timedelta <= datetime.timedelta(hours=1)]
        for i, row in good_timedelta.iterrows():
            if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
                yield i, row

    def add_mersi_info(self, mersi_dts: list[datetime.datetime], filter_na=True) -> None:
        for mersi_dt in tqdm.tqdm(mersi_dts, desc="Adding MERSI info"):
            image = MERSIImage.from_dt(mersi_dt, "8")
            for i, row in self.iterate_rows_timedelta_within_image(image):
                site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])
                self.df.loc[i, "mersi_t"] = mersi_dt
                self.df.loc[i, "mersi_minutes_diff_aeronet"] = (image.dt - row["aeronet_t"]).total_seconds() // 60
                self.df.loc[i, "mersi_minutes_diff_modis"] = (image.dt - row["modis_t"]).total_seconds() // 60
                self.df.loc[i, "mersi_senz"] = image.sensor_zenith[site_i, site_j] / 100
                self.df.loc[i, "mersi_sena"] = image.sensor_azimuth[site_i, site_j] / 100
                self.df.loc[i, "mersi_solz"] = image.solar_zenith[site_i, site_j] / 100
                self.df.loc[i, "mersi_sola"] = image.solar_azimuth[site_i, site_j] / 100
                self.df.loc[i, "mersi_lat"] = image.latitude[site_i, site_j]
                self.df.loc[i, "mersi_lon"] = image.longitude[site_i, site_j]

        if filter_na:
            self.df = self.df[self.df["mersi_t"].notna()]

    def add_modis_geometry(self) -> None:
        pass

    def add_mersi_areas(self, mersi_bands: list[str], filter_na=True) -> None:
        for band in mersi_bands:
            wl = MERSI_BANDS_WAVELEN[band]
            self.df[f"mersi_counts[{wl}nm]"] = None
            self.df[f"mersi_radiance[{wl}nm]"] = None
            self.df[f"mersi_reflectance[{wl}nm]"] = None
            self.df[f"mersi_apparent_reflectance[{wl}nm]"] = None
        self.df["mersi_mask"] = None

        for i, row in tqdm.tqdm(self.df.iterrows(), desc="Adding MERSI areas", total=len(self.df)):
            mersi_dt = row["mersi_t"]
            for band in mersi_bands:
                image = MERSIImage.from_dt(mersi_dt, band)
                wl = image.wavelength
                site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])

                # Вырезаем окно вокруг станции
                radius = 2
                area_idx = [
                    slice(max(0, site_i - radius), site_i + radius + 1),
                    slice(max(0, site_j - radius), site_j + radius + 1),
                ]

                good_pixels_mask = homogeneous_pixels_mask(image, area_idx)
                if good_pixels_mask is None:
                    continue

                counts = image.counts[*area_idx][:].copy()
                radiance = image.radiance_slice(area_idx)[:].copy()
                reflectance = image.reflectance_slice(area_idx)[:].copy()
                apparent_reflectance = image.apparent_reflectance_slice(area_idx)[:].copy()

                values = self.df.loc[i].to_dict()
                values.update({
                    "mersi_mask": good_pixels_mask,
                    f"mersi_counts[{wl}nm]": counts,
                    f"mersi_radiance[{wl}nm]": radiance,
                    f"mersi_reflectance[{wl}nm]": reflectance,
                    f"mersi_apparent_reflectance[{wl}nm]": apparent_reflectance,
                })
                self.df.loc[i] = values

                self.df.loc[i, f"mersi_n_good_pixels"] = good_pixels_mask.sum()
                self.df.loc[i, f"mersi_counts_mean[{wl}nm]"] = counts[good_pixels_mask].mean()
                self.df.loc[i, f"mersi_counts_std[{wl}nm]"] = counts[good_pixels_mask].std()
                self.df.loc[i, f"mersi_radiance_mean[{wl}nm]"] = radiance[good_pixels_mask].mean()
                self.df.loc[i, f"mersi_radiance_std[{wl}nm]"] = radiance[good_pixels_mask].std()
                self.df.loc[i, f"mersi_reflectance_mean[{wl}nm]"] = reflectance[good_pixels_mask].mean()
                self.df.loc[i, f"mersi_reflectance_std[{wl}nm]"] = reflectance[good_pixels_mask].std()
                self.df.loc[i, f"mersi_apparent_reflectance_mean[{wl}nm]"] = apparent_reflectance[good_pixels_mask].mean()
                self.df.loc[i, f"mersi_apparent_reflectance_std[{wl}nm]"] = apparent_reflectance[good_pixels_mask].std()

        if filter_na:
            self.df = self.df[self.df["mersi_counts_mean[412nm]"].notna()]

    def add_mersi_6S(self, mersi_bands: list[str]) -> None:
        for band in mersi_bands:
            wl = MERSI_BANDS_WAVELEN[band]
            self.df[f"mersi_6S[{wl}nm]"] = None
        for i, row in tqdm.tqdm(self.df.iterrows(), desc="Adding MERSI 6S", total=len(self.df)):
            for band in mersi_bands:
                wl = MERSI_BANDS_WAVELEN[band]
                image = MERSIImage.from_dt(row["mersi_t"], band)
                out = self._get_mersi_6S_output(row, image)
                values = self.df.loc[i].to_dict()
                values.update({f"mersi_6S[{wl}nm]": out.__dict__})
                self.df.loc[i] = values

    def add_modis_6S(self, modis_bands: list[str]) -> None:
        for band in modis_bands:
            wl = MODIS_BANDS_WAVELEN[band]
            self.df[f"modis_6S[{wl}nm]"] = None
        for i, row in tqdm.tqdm(self.df.iterrows(), desc="Adding MODIS 6S", total=len(self.df)):
            for band in modis_bands:
                wl = MODIS_BANDS_WAVELEN[band]
                out = self._get_modis_6S_output(row, band)
                values = self.df.loc[i].to_dict()
                values.update({f"modis_6S[{wl}nm]": out.__dict__})
                self.df.loc[i] = values

    def _get_mersi_6S_output(
            self,
            row: pd.Series,
            image: MERSIImage,
    ):
        site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])
        aot550 = row["aeronet_Aerosol_Optical_Depth[551nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[555nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[560nm]"]

        out = atmosphere_correction(
            radiance=row[f"mersi_radiance_mean[{image.wavelength}nm]"],
            wavelength=SRF.mersi_2_srf.MERSI_6S_WV[image.band],
            pixel_lat=image.latitude[site_i, site_j],
            pixel_lon=image.longitude[site_i, site_j],
            dt=image.dt,
            view_zenith=image.sensor_zenith[site_i, site_j] / 100,
            view_azimuth=image.sensor_azimuth[site_i, site_j] / 100,
            aot550=aot550,
            wind_speed=row["aeronet_Wind_Speed(m/s)"],
            chlorophyll=row["aeronet_chlor_a_from_rrs"],
        )
        return out

    def _get_modis_6S_output(
            self,
            row: pd.Series,
            band: str,
    ):
        aot550 = row["aeronet_Aerosol_Optical_Depth[551nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[555nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[560nm]"]

        out = atmosphere_correction(
            radiance=row[f"nir_Lt_{MODIS_BANDS_WAVELEN[band]}_mean"],
            wavelength=SRF.modis_aqua_srf.MODIS_6S_WV[band],
            pixel_lat=row["aeronet_lat"],
            pixel_lon=row["aeronet_lon"],
            dt=row["modis_t"],
            view_zenith=row["modis_zenith"],
            view_azimuth=row["modis_azimuth"],
            aot550=aot550,
            wind_speed=row["aeronet_Wind_Speed(m/s)"],
            chlorophyll=row["aeronet_chlor_a_from_rrs"],
        )
        return out

    def save(self, path: str) -> None:
        with open(path, "wb") as file:
            pickle.dump(self.df, file)

    @classmethod
    def load(cls, path: str):
        df = pd.read_pickle(path)
        return cls(df)


if __name__ == '__main__':
    INPUT_PATH = paths.DATA_DIR / "data.csv"
    OUTPUT_PATH = paths.DATA_DIR / "data_with_mersi.pickle"

    df = pd.read_csv(INPUT_PATH, sep="\t")
    df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
    df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
    df = df[df["modis_zenith"].notna()]
    p = TablePrecompute(df)
    mersi_dts = MERSIImage.all_dts()
    MERSI_BANDS = ["8", "9", "10", "11", "12", "13", "14", "15"]
    MODIS_BANDS = ["8", "9", "10", "11", "12", "13lo", "14lo", "15", "16"]

    p.add_mersi_info(mersi_dts, filter_na=True)
    p.save(OUTPUT_PATH)

    p.add_mersi_areas(MERSI_BANDS, filter_na=True)
    p.save(OUTPUT_PATH)

    p.add_mersi_6S(MERSI_BANDS)
    p.save(OUTPUT_PATH)

    p.add_modis_6S(MODIS_BANDS)
    p.save(OUTPUT_PATH)
