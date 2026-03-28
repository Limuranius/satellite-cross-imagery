import datetime
import os.path
import pickle
from collections import defaultdict

import numpy as np
import tqdm
import SRF

# [469,555]
MODIS_OC2_COEFFS = (0.1464, -1.7953, 0.9718, -0.8319, -0.8073)

# [443,488,547]
MODIS_OC3_COEFFS = (0.2424, -2.7423, 1.8017, 0.0015, -1.228)

# [412,443,488,547]
MODIS_OC4_COEFFS = (0.27015, -2.47936, 1.53752, -0.13967, -0.66166)


def chl_oc2(rrs, coeffs=MODIS_OC2_COEFFS):
    return 10 ** (
            coeffs[0] +
            coeffs[1] * np.log10(rrs[0] / rrs[1]) ** 1 +
            coeffs[2] * np.log10(rrs[0] / rrs[1]) ** 2 +
            coeffs[3] * np.log10(rrs[0] / rrs[1]) ** 3 +
            coeffs[4] * np.log10(rrs[0] / rrs[1]) ** 4
    )


def chl_oc3(rrs, coeffs=MODIS_OC3_COEFFS):
    max_blue = np.maximum(rrs[0], rrs[1])
    return 10 ** (
            coeffs[0] +
            coeffs[1] * np.log10(max_blue / rrs[2]) ** 1 +
            coeffs[2] * np.log10(max_blue / rrs[2]) ** 2 +
            coeffs[3] * np.log10(max_blue / rrs[2]) ** 3 +
            coeffs[4] * np.log10(max_blue / rrs[2]) ** 4
    )

    # f(x) = 10 ^ (a0 + a1 * log10(x) + a2 * log10(x) ^ 2 + a3 * log10(x) ^ 3 + a4 * log10(x) ^ 4)


def chl_oc4(rrs, coeffs=MODIS_OC4_COEFFS):
    max_blue = np.maximum(rrs[0], np.maximum(rrs[1], rrs[2]))
    return 10 ** (
            coeffs[0] +
            coeffs[1] * np.log10(max_blue / rrs[3]) ** 1 +
            coeffs[2] * np.log10(max_blue / rrs[3]) ** 2 +
            coeffs[3] * np.log10(max_blue / rrs[3]) ** 3 +
            coeffs[4] * np.log10(max_blue / rrs[3]) ** 4
    )


def mersi_chlor_a(
        rrs443: np.ndarray,
        rrs490: np.ndarray,
        rrs555: np.ndarray,
        rrs670: np.ndarray,
):
    """
        Calculate chlorophyll-a in mg m^-3
        https://www.earthdata.nasa.gov/apt/documents/chlor-a/v1.0#mathematical_theory
    """
    CI = rrs555 - (rrs443 + (555 - 443) / (670 - 443) * (rrs670 - rrs443))
    chlor_a_CI = 10 ** (-0.4287 + 230.47 * CI)

    # OCx coefficients like in MODIS
    a0 = 0.26294
    a1 = -2.64669
    a2 = 1.28364
    a3 = 1.08209
    a4 = -1.76828
    max_blue = np.maximum(rrs443, rrs490)
    chlor_a_OC3 = 10 ** (
            a0 +
            a1 * np.log10(max_blue / rrs555) ** 1 +
            a2 * np.log10(max_blue / rrs555) ** 2 +
            a3 * np.log10(max_blue / rrs555) ** 3 +
            a4 * np.log10(max_blue / rrs555) ** 4
    )
    # res = chlor_a_OC3
    res = np.empty(len(chlor_a_OC3))
    res[chlor_a_OC3 > 0.35] = chlor_a_OC3[chlor_a_OC3 > 0.35]
    res[chlor_a_OC3 < 0.25] = chlor_a_CI[chlor_a_OC3 < 0.25]
    t1 = 0.25
    t2 = 0.35
    hyb = chlor_a_CI * (t2 - chlor_a_CI) / (t2 - t1) + chlor_a_OC3 * (chlor_a_CI - t1) / (t2 - t1)
    res[(chlor_a_OC3 <= 0.35) & (chlor_a_OC3 >= 0.25)] = hyb[(chlor_a_OC3 <= 0.35) & (chlor_a_OC3 >= 0.25)]
    return res


def atmosphere_correction(
        radiance: float,  # L_toa
        wavelength: "Py6S.Wavelength",
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,  # degrees
        view_azimuth: float,  # degrees
        aot550: float,
        wind_speed: float,
        chlorophyll: float,
):
    import Py6S
    s = Py6S.SixS()
    s.wavelength = wavelength
    s.geometry = Py6S.Geometry.User()
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
    s.atmos_profile = Py6S.AtmosProfile.FromLatitudeAndDate(pixel_lat, dt.date().isoformat())
    s.ground_reflectance = Py6S.GroundReflectance.HomogeneousOcean(
        wind_speed=wind_speed,
        wind_azimuth=0,
        salinity=-1,
        pigment_concentration=chlorophyll,
    )
    s.atmos_corr = Py6S.AtmosCorr.AtmosCorrBRDFFromRadiance(radiance)

    s.run()
    output = s.outputs
    return output


def calculate_mersi_chlor_with_6S(
        dt: datetime.datetime,
        radiance443: np.ndarray,
        radiance490: np.ndarray,
        radiance555: np.ndarray,
        mask: np.ndarray,
        latitude: np.ndarray,
        longitude: np.ndarray,
        sen_zen: np.ndarray,
        sen_az: np.ndarray,
        aot550: np.ndarray,
        wind_speed: np.ndarray,
        chlorophyll: np.ndarray,
):
    if not os.path.exists("cache.pickle"):
        cache = dict()
    else:
        cache = pickle.load(open("cache.pickle", "rb"))

    import SRF.mersi_2_srf
    h, w = radiance443.shape
    result = np.zeros_like(radiance443)
    pbar = tqdm.tqdm(total=mask.sum(), position=0)
    for i in range(h):
        for j in range(w):
            if not mask[i, j]:
                result[i, j] = np.nan
                continue
            coord = (latitude[i, j], longitude[i, j])
            if coord in cache:
                result[i, j] = cache[coord]
                pbar.update(1)
                continue
            rrs = []
            for mersi_band, band_radiance in zip(
                    ["9", "10", "11"],
                    [radiance443, radiance490, radiance555],
            ):
                out = atmosphere_correction(
                    radiance=band_radiance[i, j],
                    wavelength=SRF.mersi_2_srf.MERSI_6S_WV[mersi_band],
                    pixel_lat=latitude[i, j],
                    pixel_lon=longitude[i, j],
                    dt=dt,
                    view_zenith=sen_zen[i, j],
                    view_azimuth=sen_az[i, j],
                    aot550=aot550[i, j],
                    wind_speed=wind_speed[i, j],
                    chlorophyll=chlorophyll[i, j],
                )
                rrs.append(out.atmos_corrected_reflectance_brdf / np.pi)
            result[i, j] = chl_oc3(rrs)
            cache[coord] = chl_oc3(rrs)
            with open("cache.pickle", "wb") as file:
                pickle.dump(cache, file)
            pbar.update(1)
    return result


def func(
        args
):
    idx = args[0]
    kwargs = args[1]

    i = idx // kwargs["w"]
    j = idx % kwargs["w"]
    if not kwargs["mask"][i, j]:
        return np.nan, [np.nan, np.nan, np.nan]
    rrs = []

    for mersi_band, band_radiance in zip(
            ["9", "10", "11"],
            [kwargs["radiance443"], kwargs["radiance490"], kwargs["radiance555"]],
    ):
        out = atmosphere_correction(
            radiance=band_radiance[i, j],
            wavelength=SRF.mersi_2_srf.MERSI_6S_WV[mersi_band],
            pixel_lat=kwargs["latitude"][i, j],
            pixel_lon=kwargs["longitude"][i, j],
            dt=kwargs["dt"],
            view_zenith=kwargs["sen_zen"][i, j],
            view_azimuth=kwargs["sen_az"][i, j],
            aot550=kwargs["aot550"][i, j],
            wind_speed=kwargs["wind_speed"][i, j],
            chlorophyll=kwargs["chlorophyll"][i, j],
        )
        rrs.append(out.atmos_corrected_reflectance_brdf / np.pi)
    return chl_oc3(rrs), rrs


def calculate_mersi_chlor_with_6S_parallel(**kwargs):
    from multiprocessing import Pool
    h, w = kwargs["radiance443"].shape
    kwargs["w"] = w

    args = [(i, kwargs) for i in range(h * w)]
    with Pool() as p:
        result = list(tqdm.tqdm(p.imap(func, args), total=h * w, position=0))
        chl = [r[0] for r in result]
        rrs = [r[1] for r in result]
        chl = np.array(chl).reshape((h, w))
        rrs = np.array(rrs).reshape((h, w, 3))

    return chl, rrs


def __atm_corr(kwargs):
    return atmosphere_correction(**kwargs).__dict__


def modis_atmosphere_correction_parallel(
        radiance: list[float],  # L_toa
        band: str,
        pixel_lat: list[float],
        pixel_lon: list[float],
        dt: list[datetime.datetime],
        view_zenith: list[float],  # degrees
        view_azimuth: list[float],  # degrees
        aot550: list[float],
        wind_speed: list[float],
        chlorophyll: list[float],
) -> list:
    wavelength = SRF.modis_aqua_srf.MODIS_6S_WV[band]
    from multiprocessing import Pool

    args = []
    for i in range(len(radiance)):
        args.append({
            "radiance": radiance[i],
            "wavelength": wavelength,
            "pixel_lat": pixel_lat[i],
            "pixel_lon": pixel_lon[i],
            "dt": dt[i],
            "view_zenith": view_zenith[i],
            "view_azimuth": view_azimuth[i],
            "aot550": aot550[i],
            "wind_speed": wind_speed[i],
            "chlorophyll": chlorophyll[i],
        })

    with Pool(16) as p:
        result = list(tqdm.tqdm(p.imap(__atm_corr, args), total=len(radiance), position=0))
    return result