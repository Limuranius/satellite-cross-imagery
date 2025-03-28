import datetime
from Py6S import *


def atmosphere_correction(
        wv,
        pixel_lat: float,
        pixel_lon: float,
        dt: datetime.datetime,
        view_zenith: float,  # degrees
        view_azimuth: float,  # degrees
        aot550: float,
) -> float:
    s = SixS()
    s.wavelength = wv
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


    s.run()
    output = s.outputs

    return output.apparent_radiance
    # return output.atmospheric_intrinsic_radiance


wv_mersi = Wavelength(
    0.4185,
    0.466,
    [0., 0.01397515, 0.0310559, 0.07298137, 0.11801242,
     0.21583851, 0.52484472, 0.69565217, 0.70496894, 0.83229814,
     0.97515528, 0.92857143, 0.79347826, 0.74689441, 0.7515528,
     0.45652174, 0.13354037, 0.04503106, 0.02484472, 0.01397515]
)
wv_modis = Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_9)

dt = datetime.datetime(2019, 1, 14, 11, 25)
lon, lat = (28.187548, 43.039566)
zen = 30.66
az = 261.99
aot = 0.05045
rad = 114.92930910444272

print(atmosphere_correction(wv_mersi, lat, lon, dt, zen, az, aot))
print(atmosphere_correction(wv_modis, lat, lon, dt, zen, az, aot))