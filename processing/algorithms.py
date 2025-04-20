import datetime

import numpy as np


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
    res = np.empty(len(chlor_a_OC3))
    res[chlor_a_OC3 > 0.35] = chlor_a_OC3[chlor_a_OC3 > 0.35]
    res[chlor_a_OC3 < 0.25] = chlor_a_CI[chlor_a_OC3 < 0.25]
    t1 = 0.25
    t2 = 0.35
    hyb = chlor_a_CI * (t2 - chlor_a_CI) / (t2 - t1) + chlor_a_OC3 * (chlor_a_CI - t1) / (t2 - t1)
    res[(chlor_a_OC3 <= 0.35) & (chlor_a_OC3 >= 0.25)] = hyb[(chlor_a_OC3 <= 0.35) & (chlor_a_OC3 >= 0.25)]
    return res

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
) -> tuple[float, float]:
    import Py6S
    s = Py6S.SixS()
    s.wavelength = Py6S.Wavelength(
        start_wavelength=start_wavelength,
        end_wavelength=end_wavelength,
        filter=srf
    )
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

    s.atmos_corr = Py6S.AtmosCorr.AtmosCorrBRDFFromRadiance(radiance)

    s.run()
    output = s.outputs
    reflectance_corrected = output.atmos_corrected_reflectance_brdf
    radiance_corrected = radiance - output.atmospheric_intrinsic_radiance

    return reflectance_corrected, radiance_corrected
