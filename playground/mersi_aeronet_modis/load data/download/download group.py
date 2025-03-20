import datetime

from light_info.MERSIInfo import MERSIInfo
from web.downloader import download_mersi_files

dts = """
"""

dts = [datetime.datetime.fromisoformat(s) for s in dts.strip().split("\n")]
infos = MERSIInfo.from_dts(dts)
download_mersi_files(
    infos,
    download_l1=True,
    download_l1_geo=True,
    direct_download=False,
)