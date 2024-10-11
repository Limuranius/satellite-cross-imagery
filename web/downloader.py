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
        direct_download=False,
):
    if direct_download:
        for info in tqdm(infos, desc="Downloading MERSI-2 images"):
            if download_l1:
                NSMC_parser.download_dt(info.dt, NSMC_parser.DataType.L1)
            if download_l1_geo:
                NSMC_parser.download_dt(info.dt, NSMC_parser.DataType.L1_GEO)
    else:
        for info in tqdm(infos, desc="Selecting MERSI-2 images"):
            if download_l1:
                NSMC_parser.select_dt(info.dt, NSMC_parser.DataType.L1)
            if download_l1_geo:
                NSMC_parser.select_dt(info.dt, NSMC_parser.DataType.L1_GEO)
        print("Done selecting MERSI-2 images. Now go and order them at https://satellite.nsmc.org.cn/PortalSite/Data/ShoppingCart.aspx")


def download_modis_files(
        infos: list[MODISInfo],
        download_l1=True,
        download_l1_geo=False,
        download_cloud_mask=False,
):
    for info in tqdm(infos, desc="Downloading MODIS images"):
        if download_l1:
            NASA_parser.download_image(info)
        if download_l1_geo:
            NASA_parser.download_geo(info)
        if download_cloud_mask:
            NASA_parser.download_cloud_mask(info)
        # webbrowser.open(info.get_file_url())
