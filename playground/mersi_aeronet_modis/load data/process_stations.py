import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from Py6S import *
import SRF.mersi_2_srf

import calibration
from processing.MERSIImage import MERSIImage
from processing.preprocessing import get_mersi_dates


def outliers_mask(data):
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    threshold = 1.5 * iqr
    return (data < q1 - threshold) | (data > q3 + threshold)


def atmosphere_correction(
        radiance: float,
        start_wavelength: float,  # micrometers
        end_wavelength: float,  # micrometers
        srf: list[float],
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,
        view_azimuth: float,
        aot550: float,
        E0: float,
) -> tuple[np.ndarray, np.ndarray]:
    # TODO: не работает с координатами для каждого пикселя

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

    # s.ground_reflectance = GroundReflectance.HomogeneousLambertian(0.3)
    s.atmos_corr = AtmosCorr.AtmosCorrBRDFFromRadiance(radiance)

    s.run()
    output = s.outputs

    Edir = output.direct_solar_irradiance  # direct solar irradiance
    Ediff = output.diffuse_solar_irradiance  # diffuse solar irradiance
    Lp = output.atmospheric_intrinsic_radiance  # path radiance (radiance by atmosphere)
    absorb = output.trans["global_gas"].upward  # absorption transmissivity
    scatter = output.trans["total_scattering"].upward  # scattering transmissivity
    tau2 = absorb * scatter

    radiance_corrected = radiance - Lp
    ref_corr_1 = radiance_corrected * np.pi / (tau2 * (Edir + Ediff))

    ref_corr_2 = radiance_corrected * np.pi / (E0 * np.cos(np.radians(output.solar_z)) * output.transmittance_global_gas.total * output.transmittance_total_scattering.total)
    ref_corr_3 = output.atmos_corrected_reflectance_brdf

    return radiance_corrected, ref_corr_3


def process_image(
        image: MERSIImage,
        calibration_prefix: str,  # "original" or "calibrated"
):
    for i, row in iterate_rows_timedelta_within_image(image):
        site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])

        # Вырезаем окно вокруг станции
        radius = 4
        area_idx = [
            slice(max(0, site_i - radius), site_i + radius + 1),
            slice(max(0, site_j - radius), site_j + radius + 1),
        ]

        area = image.counts[*area_idx]

        # Выкидываем выбросы
        pixels = area.flatten()
        good_pixels_mask = pixels <= 4096  # Убираем битые пиксели
        good_pixels_mask &= ~outliers_mask(pixels)  # Убираем выбросы

        solz = np.radians(image.solar_zenith[*area_idx].flatten()[good_pixels_mask] / 100)
        counts = image.counts[*area_idx].flatten()[good_pixels_mask]
        radiance = image.radiance[*area_idx].flatten()[good_pixels_mask]
        radiance_norm = radiance / np.cos(solz)
        reflectance = image.reflectance[*area_idx].flatten()[good_pixels_mask]
        apparent_reflectance = image.apparent_reflectance[*area_idx].flatten()[good_pixels_mask]

        # Atmospheric correction values
        srf = SRF.mersi_2_srf.get_band(int(image.band))
        min_wl = srf[0, 0]
        max_wl = srf[-1, 0]
        srf_grid = SRF.mersi_2_srf.range_srf(int(image.band), min_wl, max_wl, 2.5)
        max_wl = srf_grid[-1, 0]
        aot550 = row["aeronet_Aerosol_Optical_Depth[551nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[555nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[560nm]"]
        radiance_corrected, reflectance_corrected = atmosphere_correction(
            radiance=radiance.mean(),
            start_wavelength=min_wl / 1000,
            end_wavelength=max_wl / 1000,
            srf=srf_grid[:, 1],
            pixel_lat=image.latitude[site_i, site_j],
            pixel_lon=image.longitude[site_i, site_j],
            dt=image.dt,
            view_zenith=image.sensor_zenith[site_i, site_j] / 100,
            view_azimuth=image.sensor_azimuth[site_i, site_j] / 100,
            aot550=aot550,
            E0=image.E0
        )

        wl = image.wavelength
        df.loc[i, f"mersi_t"] = image.dt.isoformat()
        df.loc[i, f"mersi_sensor_zenith_deg"] = image.sensor_zenith[site_i, site_j] / 100
        df.loc[i, f"mersi_sensor_azimuth_deg"] = image.sensor_azimuth[site_i, site_j] / 100
        df.loc[i, f"n_good_pixels"] = good_pixels_mask.sum()
        df.loc[i, f"mersi_{calibration_prefix}_counts_mean[{wl}nm]"] = counts.mean()
        df.loc[i, f"mersi_{calibration_prefix}_counts_std[{wl}nm]"] = counts.std()
        df.loc[i, f"mersi_{calibration_prefix}_radiance_mean[{wl}nm]"] = radiance.mean()
        df.loc[i, f"mersi_{calibration_prefix}_radiance_std[{wl}nm]"] = radiance.std()
        df.loc[i, f"mersi_{calibration_prefix}_radiance_norm_mean[{wl}nm]"] = radiance_norm.mean()
        df.loc[i, f"mersi_{calibration_prefix}_radiance_norm_std[{wl}nm]"] = radiance_norm.std()
        df.loc[i, f"mersi_{calibration_prefix}_reflectance_mean[{wl}nm]"] = reflectance.mean()
        df.loc[i, f"mersi_{calibration_prefix}_reflectance_std[{wl}nm]"] = reflectance.std()
        df.loc[i, f"mersi_{calibration_prefix}_apparent_reflectance_mean[{wl}nm]"] = apparent_reflectance.mean()
        df.loc[i, f"mersi_{calibration_prefix}_apparent_reflectance_std[{wl}nm]"] = apparent_reflectance.std()
        df.loc[i, f"mersi_{calibration_prefix}_6S_radiance_mean[{wl}nm]"] = radiance_corrected.mean()
        df.loc[i, f"mersi_{calibration_prefix}_6S_radiance_std[{wl}nm]"] = radiance_corrected.std()
        df.loc[i, f"mersi_{calibration_prefix}_6S_reflectance_mean[{wl}nm]"] = reflectance_corrected.mean()
        df.loc[i, f"mersi_{calibration_prefix}_6S_reflectance_std[{wl}nm]"] = reflectance_corrected.std()


def iterate_rows_timedelta_within_image(image: MERSIImage):
    timedelta = (df["aeronet_t"] - image.dt).abs()
    good_timedelta = df[timedelta <= datetime.timedelta(hours=1)]
    for i, row in good_timedelta.iterrows():
        if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
            yield i, row


BANDS = ["8", "9", "10", "11", "12", "13", "14", "15"]
df = pd.read_csv("data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
if __name__ == '__main__':
    mersi_dts = get_mersi_dates()
    for mersi_dt in tqdm.tqdm(mersi_dts):
        for band in BANDS:
            image = MERSIImage.from_dt(mersi_dt, band)
            process_image(image, "original")
            calibration.full_correct_image(
                image,
                remove_zebra=True,
                remove_neighbor_influence=True,
                remove_trace=True,
            )
            process_image(image, "calibrated")

    df = df[df["mersi_t"] == df["mersi_t"]]
    df.to_csv("data_with_mersi_calibrated.csv", sep="\t", index=False)
