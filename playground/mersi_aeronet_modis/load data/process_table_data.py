import datetime

import numpy as np
import pandas as pd
import tqdm
from Py6S import *

import SRF.mersi_2_srf
from processing.MERSIImage import MERSIImage
from processing.preprocessing import get_mersi_dates


def outliers_mask(data):
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    threshold = 1.5 * iqr
    return (data < q1 - threshold) | (data > q3 + threshold)


def outliers_2d_mask(data_2d: np.ndarray):
    data = data_2d.flatten()
    mask_1d = outliers_mask(data)
    return mask_1d.reshape(data_2d.shape)


def atmosphere_correction(
        radiance: float,
        start_wavelength: float,  # micrometers
        end_wavelength: float,  # micrometers
        srf: list[float],  # srf for wavelength from start to end with 2.5 nm step
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,  # degrees
        view_azimuth: float,  # degrees
        aot550: float,
) -> float:
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

    s.atmos_corr = AtmosCorr.AtmosCorrBRDFFromRadiance(radiance)

    s.run()
    output = s.outputs
    reflectance_corrected = output.atmos_corrected_reflectance_brdf

    return reflectance_corrected


def process_image(
        image: MERSIImage,
):
    for i, row in iterate_rows_timedelta_within_image(image):
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

        # Посмотреть маску хороших пикселей
        # _, ax = plt.subplots(ncols=2)
        # # ax[0].imshow(image.counts[*area_idx])
        # sns.heatmap(image.counts[*area_idx], center=0, annot=True, ax=ax[0])
        # ax[1].imshow(good_pixels_mask.reshape((5, 5)))
        # plt.show()

        # solz = np.radians(image.solar_zenith[*area_idx].flatten()[good_pixels_mask] / 100)
        counts = image.counts[*area_idx].flatten()[good_pixels_mask]
        # radiance = image.radiance[*area_idx].flatten()[good_pixels_mask]
        radiance = image.radiance_slice(area_idx).flatten()[good_pixels_mask]
        # reflectance = image.reflectance[*area_idx].flatten()[good_pixels_mask]
        reflectance = image.reflectance_slice(area_idx).flatten()[good_pixels_mask]
        # apparent_reflectance = image.apparent_reflectance[*area_idx].flatten()[good_pixels_mask]

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
        reflectance_corrected = atmosphere_correction(
            radiance=radiance.mean(),
            start_wavelength=min_wl / 1000,
            end_wavelength=max_wl / 1000,
            srf=srf_grid[:, 1],
            pixel_lat=image.latitude[site_i, site_j],
            pixel_lon=image.longitude[site_i, site_j],
            dt=image.dt,
            view_zenith=image.sensor_zenith[site_i, site_j] / 100,
            view_azimuth=image.sensor_azimuth[site_i, site_j] / 100,
            aot550=aot550
        )
        if image.dt.isoformat() == "2019-01-14T11:25:00" and image.wavelength == 443:
            print(dict(
                radiance=radiance.mean(),
                start_wavelength=min_wl / 1000,
                end_wavelength=max_wl / 1000,
                srf=srf_grid[:, 1],
                pixel_lat=image.latitude[site_i, site_j],
                pixel_lon=image.longitude[site_i, site_j],
                dt=image.dt,
                view_zenith=image.sensor_zenith[site_i, site_j] / 100,
                view_azimuth=image.sensor_azimuth[site_i, site_j] / 100,
                aot550=aot550
            ))
            print(reflectance_corrected)

        wl = image.wavelength
        df.loc[i, f"mersi_n_good_pixels"] = good_pixels_mask.sum()
        df.loc[i, f"mersi_minutes_diff_aeronet"] = (image.dt - row["aeronet_t"]).total_seconds() // 60
        df.loc[i, f"mersi_minutes_diff_modis"] = (image.dt - row["modis_t"]).total_seconds() // 60
        df.loc[i, f"mersi_t"] = image.dt.isoformat()
        df.loc[i, f"mersi_sensor_zenith_deg"] = image.sensor_zenith[site_i, site_j] / 100
        df.loc[i, f"mersi_sensor_azimuth_deg"] = image.sensor_azimuth[site_i, site_j] / 100
        df.loc[i, f"mersi_counts[{wl}nm]"] = counts.mean()
        df.loc[i, f"mersi_counts_std[{wl}nm]"] = counts.std()
        df.loc[i, f"mersi_radiance[{wl}nm]"] = radiance.mean()
        # df.loc[i, f"mersi_radiance_std[{wl}nm]"] = radiance.std()
        df.loc[i, f"mersi_reflectance[{wl}nm]"] = reflectance.mean()
        # df.loc[i, f"mersi_reflectance_std[{wl}nm]"] = reflectance.std()
        # df.loc[i, f"mersi_apparent_reflectance[{wl}nm]"] = apparent_reflectance.mean()
        # df.loc[i, f"mersi_apparent_reflectance_std[{wl}nm]"] = apparent_reflectance.std()
        # df.loc[i, f"mersi_6S_radiance[{wl}nm]"] = radiance_corrected
        # df.loc[i, f"mersi_6S_radiance_std[{wl}nm]"] = radiance_corrected.std()
        df.loc[i, f"mersi_6S_reflectance[{wl}nm]"] = reflectance_corrected
        # df.loc[i, f"mersi_6S_reflectance_std[{wl}nm]"] = reflectance_corrected.std()


def homogeneous_pixels_mask(image: MERSIImage, area_idx):
    band13 = image.get_band("13")
    area = band13.counts[*area_idx]
    pixels = area.flatten()
    good_pixels_mask = pixels <= 4096  # Убираем битые пиксели
    if pixels[good_pixels_mask].std() < 100:  # Изображение изначально было однородным
        return good_pixels_mask
    good_pixels_mask &= ~outliers_mask(pixels)  # Убираем выбросы
    if pixels[good_pixels_mask].std() < 100:
        return good_pixels_mask
    return None  # Слишком зашумлено, невозможно убрать выбросы, потому что не понятно, что является выбросом


def iterate_rows_timedelta_within_image(image: MERSIImage):
    timedelta = (df["aeronet_t"] - image.dt).abs()
    good_timedelta = df[timedelta <= datetime.timedelta(hours=1)]
    for i, row in good_timedelta.iterrows():
        if image.contains_pos(row["aeronet_lon"], row["aeronet_lat"]):
            yield i, row


BANDS = [
    "8", "9", "10", "11",
    # "12", "13", "14", "15"
]
# BANDS = ["8"]
df = pd.read_csv("data.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])
if __name__ == '__main__':
    mersi_dts = get_mersi_dates()
    for mersi_dt in tqdm.tqdm(mersi_dts):
        for band in BANDS:
            image = MERSIImage.from_dt(mersi_dt, band)
            process_image(image)

    df = df[df["mersi_t"] == df["mersi_t"]]
    df.to_csv("data_with_mersi.csv", sep="\t", index=False)
