import datetime

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
    import SRF.mersi_2_srf
    h, w = radiance443.shape
    result = np.zeros_like(radiance443)
    pbar = tqdm.tqdm(total=mask.sum(), position=0)
    for i in range(h):
        for j in range(w):
            if not mask[i, j]:
                result[i, j] = np.nan
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
            pbar.update(1)
    return result


def func(
        idx,
        w, mask, radiance443, radiance490, radiance555,
        latitude, longitude, dt, sen_zen, sen_az, aot550, wind_speed, chlorophyll
):
    i = idx // w
    j = idx % w
    print("aaa")
    if not mask[i, j]:
        return np.nan
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
    return chl_oc3(rrs)


def calculate_mersi_chlor_with_6S_parallel(
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
    from multiprocessing import Pool
    h, w = radiance443.shape

    p = Pool()
    result = list(tqdm.tqdm(p.imap(func, range(h * w)), total=h * w))
    result = np.array(result)
    result = result.reshape((h, w))

    return result
