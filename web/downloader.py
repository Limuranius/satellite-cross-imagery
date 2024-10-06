from tqdm import tqdm
from web import NSMC_parser
from web import NASA_parser
from light_info.MERSIInfo import MERSIInfo
from light_info.MODISInfo import MODISInfo


def download_mersi_files(
        infos: list[MERSIInfo],
        download_l1=True,
        download_l1_geo=False,
):
    for info in tqdm(infos, desc="Downloading MERSI-2 images"):
        if download_l1:
            NSMC_parser.download_dt(info.dt, NSMC_parser.DataType.L1)
        if download_l1_geo:
            NSMC_parser.download_dt(info.dt, NSMC_parser.DataType.L1_GEO)


def download_modis_files(infos: list[MODISInfo]):
    for info in tqdm(infos, desc="Downloading MODIS images"):
        NASA_parser.download_image(info)
