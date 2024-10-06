import os

import requests

import paths
from light_info.MODISInfo import MODISInfo
from web.utils import download_file

session = requests.Session()
cookies_str = input("Enter cookies from https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MYD021KM: ")
for pair in cookies_str.split("; "):
    key, value = pair.split("=", maxsplit=1)
    session.cookies.set(key, value)


def download_image(info: MODISInfo):
    download_file(
        url=info.get_file_url(),
        output_path=os.path.join(paths.MODIS_L1B_DIR, info.filename),
        session=session,
    )
