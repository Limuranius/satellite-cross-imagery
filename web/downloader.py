from tqdm import tqdm
from web import NSMC_parser
from web import NASA_parser
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo
import webbrowser


def download_mersi_files(
        infos: list[MERSIInfo],
        download_l1=True,
        download_l1_geo=False,
):
    for info in tqdm(infos, desc="Selecting MERSI-2 images"):
        if download_l1:
            NSMC_parser.select_dt(info.dt, NSMC_parser.DataType.L1)
        if download_l1_geo:
            NSMC_parser.select_dt(info.dt, NSMC_parser.DataType.L1_GEO)
    print("Done selecting MERSI-2 images. Now go and order them at https://satellite.nsmc.org.cn/PortalSite/Data/ShoppingCart.aspx")


def download_modis_files(infos: list[MODISInfo]):
    for info in tqdm(infos, desc="Downloading MODIS images"):
        # NASA_parser.download_image(info)
        webbrowser.open(info.get_file_url())
