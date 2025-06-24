import datetime
import multiprocessing

import matplotlib.pyplot as plt
import numpy as np
from Py6S import *


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

    s.atmos_profile = AtmosProfile.FromLatitudeAndDate(
        pixel_lat,
        dt.date().isoformat(),
    )

    s.aero_profile = AeroProfile.User(water=0.5, oceanic=0.5)

    s.atmos_corr = AtmosCorr.AtmosCorrLambertianFromRadiance(radiance)

    s.run()
    output = s.outputs
    reflectance_corrected = output.atmos_corrected_reflectance_lambertian

    return reflectance_corrected



srf = [0., 0.01397515, 0.0310559, 0.07298137, 0.11801242,
       0.21583851, 0.52484472, 0.69565217, 0.70496894, 0.83229814,
       0.97515528, 0.92857143, 0.79347826, 0.74689441, 0.7515528,
       0.45652174, 0.13354037, 0.04503106, 0.02484472, 0.01397515]
start = 0.4185
end = 0.466
dt = datetime.datetime(2019, 1, 14, 11, 25)
lonlat = (28.187548, 43.039566)
zen = 30.66
az = 261.99
aot = 0.05045
rad = 114.92930910444272

print(atmosphere_correction(
    radiance=rad,
    start_wavelength=start,
    end_wavelength=end,
    srf=srf,
    pixel_lat=lonlat[1],
    pixel_lon=lonlat[0],
    dt=dt,
    view_zenith=zen,
    view_azimuth=az,
    aot550=aot
))

# 0.42379
# 0.4243

# refl = []
# for rad in np.linspace(rad1, rad2, 20):
#     refl.append(atmosphere_correction(rad, start, end, srf, lonlat1[1], lonlat1[0], dt, zen1, az1, aot1))
# plt.plot(refl)
# plt.show()