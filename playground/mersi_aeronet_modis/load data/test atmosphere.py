import datetime

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

    s.atmos_corr = AtmosCorr.AtmosCorrBRDFFromRadiance(radiance)

    s.run()
    output = s.outputs
    reflectance_corrected = output.atmos_corrected_reflectance_brdf

    return reflectance_corrected


srf = [0., 0.01397515, 0.0310559, 0.07298137, 0.11801242,
       0.21583851, 0.52484472, 0.69565217, 0.70496894, 0.83229814,
       0.97515528, 0.92857143, 0.79347826, 0.74689441, 0.7515528,
       0.45652174, 0.13354037, 0.04503106, 0.02484472, 0.01397515]
start = 0.4185
end = 0.466
dt = datetime.datetime(2019, 1, 14, 11, 25)
lonlat1 = (28.187548, 43.039566)
lonlat2 = (29.36602, 44.605766)
zen1 = 30.66
az1 = 261.99
zen2 = 37.81
az2 = 262.95
aot1 = 0.05045
aot2 = 0.051567
rad1 = 114.92930910444272
rad2 = 197.32263197355002

# print(atmosphere_correction(rad1, start, end, srf, lonlat1[1], lonlat1[0], dt, zen1, az1, aot1))
# print(atmosphere_correction(rad2, start, end, srf, lonlat2[1], lonlat2[0], dt, zen2, az2, aot2))

refl = []
for rad in np.linspace(rad1, rad2, 20):
    refl.append(atmosphere_correction(rad, start, end, srf, lonlat1[1], lonlat1[0], dt, zen1, az1, aot1))

plt.plot(refl)
plt.show()