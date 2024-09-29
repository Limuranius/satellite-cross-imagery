import datetime

from tqdm import tqdm

from MERSIInfo import MERSIInfo
from MODISInfo import MODISInfo
import select_MERSI_files
import webbrowser


def download_mersi_files(infos: list[MERSIInfo]):
    for info in tqdm(infos):
        select_MERSI_files.select_dt(info.dt)
    print("Done selecting files! Go to https://satellite.nsmc.org.cn/PortalSite/Data/ShoppingCart.aspx")


def download_modis_files(infos: list[MODISInfo]):
    input("Log into https://ladsweb.modaps.eosdis.nasa.gov/ and press Enter")
    for info in infos:
        webbrowser.open(info.get_file_url())
