import datetime
import json
import os
from enum import Enum, auto
from web.utils import download_file
import paths

import requests


class DataType(Enum):
    L1 = auto()
    L1_GEO = auto()

    def suffix(self) -> str:
        return {
            DataType.L1: "1000M",
            DataType.L1_GEO: "GEO1K"
        }[self]

    def output_dir(self) -> str:
        return {
            DataType.L1: paths.MERSI_L1_DIR,
            DataType.L1_GEO: paths.MERSI_L1_GEO_DIR,
        }[self]


session = requests.Session()
cookies_str = input("Enter cookies from https://satellite.nsmc.org.cn: ")
for pair in cookies_str.split("; "):
    key, value = pair.split("=", maxsplit=1)
    session.cookies.set(key, value)


def select_dt(
        dt: datetime.datetime,
        data_type: DataType,
) -> None:
    headers = {
        "Content-Type": "application/json;charset=utf-8",
    }

    filename_fmt = f"FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_{data_type.suffix()}_MS.HDF"
    post_data = {
        "filename": dt.strftime(filename_fmt),
        "ischecked": True,
        "satellitecode": "FY3D",
        "datalevel": "L1"
    }

    session.post(
        "https://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/selectOne",
        headers=headers,
        data=json.dumps(post_data)
    )


def download_dt(
        dt: datetime.datetime,
        data_type: DataType,
) -> None:
    filename_fmt = f"FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_{data_type.suffix()}_MS.HDF"
    filename = dt.strftime(filename_fmt)
    url = f"https://satellite.nsmc.org.cn/PortalSite/Data/RealDataDownload.aspx?fileName={filename}"

    download_file(
        url,
        output_path=os.path.join(data_type.output_dir(), filename),
        session=session
    )
