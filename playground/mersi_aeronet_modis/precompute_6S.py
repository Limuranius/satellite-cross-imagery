import collections
import datetime
import pickle

import numpy as np
import pandas as pd
import tqdm
from Py6S import *

import paths
from processing.MERSIImage import MERSIImage
import SRF.mersi_2_srf


def atmosphere_correction(
        start_wavelength: float,  # micrometers
        end_wavelength: float,  # micrometers
        srf: list[float],  # srf for wavelength from start to end with 2.5 nm step
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,  # degrees
        view_azimuth: float,  # degrees
        aot550: float,
        wind_speed: float,
        chlorophyll: float,
):
    s = SixS()
    s.wavelength = Wavelength(
        start_wavelength=start_wavelength,
        end_wavelength=end_wavelength,
        filter=srf
    )
    s.geometry = Geometry.User()
    s.geometry.from_time_and_location(
        lat=pixel_lat,
        lon=pixel_lon,
        datetimestring=dt.isoformat(),
        view_z=view_zenith,
        view_a=view_azimuth,
    )
    s.aot550 = aot550
    s.altitudes.set_target_sea_level()
    s.altitudes.set_sensor_satellite_level()
    s.atmos_profile = AtmosProfile.FromLatitudeAndDate(pixel_lat, dt.date().isoformat())
    s.ground_reflectance = GroundReflectance.HomogeneousOcean(
        wind_speed=wind_speed,
        wind_azimuth=0,
        salinity=-1,
        pigment_concentration=chlorophyll,
    )

    s.run()
    output = s.outputs
    return output


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



class Precompute6S:
    mersi_dts: list[datetime.datetime]
    mersi_bands: list[str]
    df: pd.DataFrame

    def __init__(self, mersi_dts, mersi_bands, df):
        self.mersi_dts = mersi_dts
        self.mersi_bands = mersi_bands
        self.df = df

    def iterate_rows_timedelta_within_image(self, image: MERSIImage):
        timedelta = (self.df["aeronet_t"] - image.dt).abs()
        good_timedelta = self.df[timedelta <= datetime.timedelta(hours=1)]
        for i, row in good_timedelta.iterrows():
            if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
                yield i, row

    def get_6S_output(
            self,
            row: pd.Series,
            image: MERSIImage,
            band: str
    ):
        site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])
        srf = SRF.mersi_2_srf.get_band(int(band))
        min_wl = srf[0, 0]
        max_wl = srf[-1, 0]
        srf_grid = SRF.mersi_2_srf.range_srf(int(band), min_wl, max_wl, 2.5)
        max_wl = srf_grid[-1, 0]
        aot550 = row["aeronet_Aerosol_Optical_Depth[551nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[555nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[560nm]"]

        out = atmosphere_correction(
            start_wavelength=min_wl / 1000,
            end_wavelength=max_wl / 1000,
            srf=srf_grid[:, 1],
            pixel_lat=image.latitude[site_i, site_j],
            pixel_lon=image.longitude[site_i, site_j],
            dt=image.dt,
            view_zenith=image.sensor_zenith[site_i, site_j] / 100,
            view_azimuth=image.sensor_azimuth[site_i, site_j] / 100,
            aot550=aot550,
            wind_speed=row["aeronet_Wind_Speed(m/s)"],
            chlorophyll=row["aeronet_Chlorophyll-a"],
        )
        return out

    def process(self):
        results = collections.defaultdict(list)  # MERSI band: (mersi_t, aeronet_t, 6S_output)

        for mersi_dt in tqdm.tqdm(mersi_dts):
            for band in BANDS:
                image = MERSIImage.from_dt(mersi_dt, band)
                for i, row in self.iterate_rows_timedelta_within_image(image):
                    out = self.get_6S_output(row, image, band)
                    results[band].append({
                        "mersi_t": image.dt,
                        "aeronet_t": row["aeronet_t"].to_pydatetime(),
                        "6S_output": out.__dict__,
                    })
        return results

    def add_mersi_to_table(self):
        for mersi_dt in tqdm.tqdm(mersi_dts):
            for band in BANDS:
                image = MERSIImage.from_dt(mersi_dt, band)
                for i, row in self.iterate_rows_timedelta_within_image(image):
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

                    counts = image.counts[*area_idx][good_pixels_mask]
                    radiance = image.radiance_slice(area_idx)[good_pixels_mask]
                    reflectance = image.reflectance_slice(area_idx)[good_pixels_mask]
                    # apparent_reflectance = image.apparent_reflectance[*area_idx][good_pixels_mask]

                    wl = image.wavelength
                    df.loc[i, f"mersi_n_good_pixels"] = good_pixels_mask.sum()
                    df.loc[i, f"mersi_minutes_diff_aeronet"] = (image.dt - row["aeronet_t"]).total_seconds() // 60
                    df.loc[i, f"mersi_minutes_diff_modis"] = (image.dt - row["modis_t"]).total_seconds() // 60
                    df.loc[i, f"mersi_t"] = image.dt.isoformat()
                    df.loc[i, f"mersi_sensor_zenith_deg"] = image.sensor_zenith[site_i, site_j] / 100
                    df.loc[i, f"mersi_sensor_azimuth_deg"] = image.sensor_azimuth[site_i, site_j] / 100
                    df.loc[i, f"mersi_solar_zenith_deg"] = image.solar_zenith[site_i, site_j] / 100
                    df.loc[i, f"mersi_lat"] = image.latitude[site_i, site_j]
                    df.loc[i, f"mersi_lon"] = image.longitude[site_i, site_j]
                    df.loc[i, f"mersi_counts[{wl}nm]"] = counts.mean()
                    df.loc[i, f"mersi_counts_std[{wl}nm]"] = counts.std()
                    df.loc[i, f"mersi_radiance[{wl}nm]"] = radiance.mean()
                    df.loc[i, f"mersi_radiance_std[{wl}nm]"] = radiance.std()
                    df.loc[i, f"mersi_reflectance[{wl}nm]"] = reflectance.mean()
                    # df.loc[i, f"mersi{suffix}_reflectance_std[{wl}nm]"] = reflectance.std()
                    # df.loc[i, f"mersi{suffix}_apparent_reflectance[{wl}nm]"] = apparent_reflectance.mean()
                    # df.loc[i, f"mersi{suffix}_apparent_reflectance_std[{wl}nm]"] = apparent_reflectance.std()

if __name__ == '__main__':
    INPUT_PATH = paths.DATA_DIR / "data.csv"
    OUTPUT_PATH = paths.DATA_DIR / "data_with_mersi_2.csv"

    df = pd.read_csv(INPUT_PATH, sep="\t")
    df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
    df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
    df = df[df["modis_zenith"].notna()]
    mersi_dts = MERSIImage.all_dts()
    BANDS = [
        "8", "9", "10", "11", "12", "13", "14", "15", "16",
    ]
    p = Precompute6S(mersi_dts, BANDS, df)
    # results = p.process()
    p.add_mersi_to_table()

    df = df[df["mersi_t"] == df["mersi_t"]]
    df.to_csv(OUTPUT_PATH, sep="\t", index=False)

    # with open("atmosphere.pkl", "wb") as file:
    #     pickle.dump(results, file)
