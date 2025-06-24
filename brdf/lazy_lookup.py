import pathlib
import pickle

import numpy as np
import pandas as pd
import tqdm
from Py6S import *
import paths

# Loading all wavelength to Py6S format
import SRF.mersi_2_srf

MERSI_WV = {}
for band in range(1, 20):
    srf = SRF.mersi_2_srf.get_band(int(band))
    min_wl = srf[0, 0]
    max_wl = srf[-1, 0]
    srf_grid = SRF.mersi_2_srf.range_srf(int(band), min_wl, max_wl, 2.5)
    max_wl = srf_grid[-1, 0]
    wl = Wavelength(
        start_wavelength=min_wl / 1000,
        end_wavelength=max_wl / 1000,
        filter=srf_grid[:, 1],
    )
    MERSI_WV[str(band)] = wl

MODIS_WV = {
    "8": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_8),
    "9": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_9),
    "10": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_10),
    "11": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_11),
    "12": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_12),
    "13lo": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_13),
    "14lo": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_14),
    "15": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_15),
    "16": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_16),
}

MAX_DIST_TO_LOOKUP = 0.25

# Loading tables
mersi_table_path = paths.DIR_PATH / "brdf" / "tables" / "lazy_table_mersi.pickle"
modis_table_path = paths.DIR_PATH / "brdf" / "tables" / "lazy_table_modis.pickle"
if not mersi_table_path.exists():
    mersi_table = dict()
    for band in range(1, 20):
        band = str(band)
        mersi_table[band] = np.zeros((1, 5))
        mersi_table[band][0, 4] = 1.0
    with open(mersi_table_path, "wb") as file:
        pickle.dump(mersi_table, file)
else:
    with open(mersi_table_path, "rb") as file:
        mersi_table = pickle.load(file)

if not modis_table_path.exists():
    modis_table = dict()
    for band in MODIS_WV:
        modis_table[band] = np.zeros((1, 5))
        modis_table[band][0, 4] = 1.0
    with open(modis_table_path, "wb") as file:
        pickle.dump(modis_table, file)
else:
    with open(modis_table_path, "rb") as file:
        modis_table = pickle.load(file)


def _brdf_factor(
        solar_z: float,  # solar zenith angle
        solar_a: float,  # solar azimuth angle
        view_z: float,  # view zenith angle
        view_a: float,  # view azimuth angle
        wavelength: Wavelength,
):
    s = SixS()
    s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
    s.aero_profile = AeroProfile.PredefinedType(AeroProfile.Maritime)
    s.geometry = Geometry.User()
    s.geometry.solar_z = solar_z
    s.geometry.solar_a = solar_a
    s.geometry.view_z = view_z
    s.geometry.view_a = view_a
    s.wavelength = wavelength
    s.altitudes.set_sensor_satellite_level()

    # Set water surface with rough ocean BRDF
    s.ground_reflectance = GroundReflectance.HomogeneousOcean(
        wind_speed=1.0,
        pigment_concentration=5.0,
        salinity=-1,
        wind_azimuth=0,
    )

    # Get modeled radiance without BRDF (nadir view)
    s.geometry.view_z = 0  # Nadir
    s.run()
    nadir_radiance = s.outputs.apparent_radiance

    # Get modeled radiance with actual angles
    s.geometry.view_z = view_z
    s.run()
    angular_radiance = s.outputs.apparent_radiance

    factor = nadir_radiance / angular_radiance
    return factor


def compute_brdf(
        solar_z: float,
        solar_a: float,
        view_z: float,
        view_a: float,
        band: str,
        satellite: str,  # MERSI or MODIS
) -> float:
    row = [solar_z, solar_a, view_z, view_a]
    if satellite == "MERSI":
        band_table = mersi_table[band]
    else:
        band_table = modis_table[band]
    dist = np.linalg.norm(row - band_table[:, :-1], axis=1)
    closest_i = dist.argmin()
    closest_dist = dist[closest_i]
    if closest_dist <= MAX_DIST_TO_LOOKUP:
        return band_table[closest_i, 4]
    else:
        if satellite == "MERSI":
            wl = MERSI_WV[band]
        else:
            wl = MODIS_WV[band]
        factor = _brdf_factor(
            solar_z=solar_z,
            solar_a=solar_a,
            view_z=view_z,
            view_a=view_a,
            wavelength=wl,
        )
        if satellite == "MERSI":
            mersi_table[band] = np.vstack([
                band_table,
                row + [factor]
            ])
            with open(mersi_table_path, "wb") as file:
                pickle.dump(mersi_table, file)
        else:
            modis_table[band] = np.vstack([
                band_table,
                row + [factor]
            ])
            with open(modis_table_path, "wb") as file:
                pickle.dump(modis_table, file)
        return factor


def fix_brdf_batch(
        radiance: pd.Series | np.ndarray,
        solar_z: pd.Series | np.ndarray,
        solar_a: pd.Series | np.ndarray,
        view_z: pd.Series | np.ndarray,
        view_a: pd.Series | np.ndarray,
        band: str,
        satellite: str,  # MERSI or MODIS
) -> np.ndarray:
    results = []
    for rad, solz, sola, senz, sena in tqdm.tqdm(
            zip(radiance, solar_z, solar_a, view_z, view_a),
            desc="Correcting BRDF",
            total=len(radiance),
    ):
        factor = compute_brdf(solz, sola, senz, sena, band=band, satellite=satellite)
        results.append(rad * factor)
    return np.array(results)
