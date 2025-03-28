import pandas as pd
import tqdm
from Py6S import *
import datetime
import SRF.modis_aqua_srf


WL_TO_BAND = {
    412: 8,
    443: 9,
    469: 10,
    488: 10,
    531: 11,
    547: 12,
    555: 12,
    645: 13,
    667: 13,
    678: 14,
    748: 15,
}


def atmosphere_correction(
        radiance: float,
        band: int,
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,  # degrees
        view_azimuth: float,  # degrees
        aot550: float,
) -> tuple[float, float]:
    s = SixS()
    s.wavelength = Wavelength({
        1: PredefinedWavelengths.ACCURATE_MODIS_AQUA_1,
        2: PredefinedWavelengths.ACCURATE_MODIS_AQUA_2,
        3: PredefinedWavelengths.ACCURATE_MODIS_AQUA_3,
        4: PredefinedWavelengths.ACCURATE_MODIS_AQUA_4,
        5: PredefinedWavelengths.ACCURATE_MODIS_AQUA_5,
        6: PredefinedWavelengths.ACCURATE_MODIS_AQUA_6,
        7: PredefinedWavelengths.ACCURATE_MODIS_AQUA_7,
        8: PredefinedWavelengths.ACCURATE_MODIS_AQUA_8,
        9: PredefinedWavelengths.ACCURATE_MODIS_AQUA_9,
        10: PredefinedWavelengths.ACCURATE_MODIS_AQUA_10,
        11: PredefinedWavelengths.ACCURATE_MODIS_AQUA_11,
        12: PredefinedWavelengths.ACCURATE_MODIS_AQUA_12,
        13: PredefinedWavelengths.ACCURATE_MODIS_AQUA_13,
        14: PredefinedWavelengths.ACCURATE_MODIS_AQUA_14,
        15: PredefinedWavelengths.ACCURATE_MODIS_AQUA_15,
        16: PredefinedWavelengths.ACCURATE_MODIS_AQUA_16,
    }[band])

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
    radiance_corrected = radiance - output.atmospheric_intrinsic_radiance

    return reflectance_corrected, radiance_corrected

df = pd.read_csv("data_with_mersi.csv", sep="\t")
df["modis_t"] = pd.to_datetime(df["modis_t"], format="mixed")
df["aeronet_t"] = pd.to_datetime(df["aeronet_t"])

for i, row in tqdm.tqdm(df.iterrows(), total=len(df)):
    for wl in WL_TO_BAND:
        band = WL_TO_BAND[wl]
        aot550 = row["aeronet_Aerosol_Optical_Depth[551nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[555nm]"]
        if aot550 != aot550:
            aot550 = row["aeronet_Aerosol_Optical_Depth[560nm]"]
        reflectance_corrected, radiance_corrected = atmosphere_correction(
            radiance=row[f"nir_Lt_{wl}_mean"],
            band=band,
            pixel_lat=row["modis_lat"],
            pixel_lon=row["modis_lon"],
            dt=row["modis_t"],
            view_zenith=row["modis_zenith"],
            view_azimuth=row["modis_azimuth"],
            aot550=aot550
        )
        df.loc[i, f"modis_{wl}_6S_Rrs"] = reflectance_corrected
        df.loc[i, f"modis_{wl}_6S_Lt"] = radiance_corrected


df.to_csv("data_with_mersi.csv", sep="\t", index=False)