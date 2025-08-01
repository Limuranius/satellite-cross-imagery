import datetime
import os

import requests

import paths
from light_info.MODISInfo import MODISInfo
from web.web_utils import download_file


session = None
def require_cookie(func):
    def wrapped(*args, **kwargs):
        global session
        if session is None:
            session = requests.Session()
            cookies_str = input("Enter cookies from https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MYD021KM: ")
            for pair in cookies_str.split("; "):
                key, value = pair.split("=", maxsplit=1)
                session.cookies.set(key, value)
        return func(*args, **kwargs)
    return wrapped


@require_cookie
def download_image(info: MODISInfo):
    download_file(
        url=info.get_file_url(),
        output_path=os.path.join(paths.MODIS_L1B_DIR, info.filename),
        session=session,
    )

@require_cookie
def download_geo(info: MODISInfo):
    download_file(
        url=info.get_geo_file_url(),
        output_path=os.path.join(paths.MODIS_L1B_GEO_DIR, info.geo_filename),
        session=session,
    )

@require_cookie
def download_cloud_mask(info: MODISInfo):
    download_file(
        url=info.get_cloud_mask_file_url(),
        output_path=os.path.join(paths.MODIS_CLOUD_MASK_DIR, info.cloud_mask_filename),
        session=session,
    )

@require_cookie
def download_chlor_a(dt: datetime.datetime):
    filename = dt.strftime("AQUA_MODIS.%Y%m%d.L3m.DAY.CHL.chlor_a.4km.nc")
    url = "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/" + filename
    print("Downloading", url)
    # download_file(
    #     url=url,
    #     output_path=paths.MODIS_CHLOROPHYL_DIR / filename,
    #     session=session,
    # )
