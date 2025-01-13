import datetime
import json
import os
import re
from enum import Enum, auto
from io import BytesIO

import grequests
import numpy as np
import requests
from PIL import Image
from tqdm import tqdm

import paths
from web.utils import download_file


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


def get_preview(dt: datetime.datetime) -> np.ndarray:
    url_fmt = "https://img.nsmc.org.cn/IMG_LIB/FY3D/FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF/%Y%m%d/FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF.jpg"
    image_url = dt.strftime(url_fmt)
    img_resp = requests.get(image_url)
    img = Image.open(BytesIO(img_resp.content))
    return np.array(img)


def request_dts_infos(dts: list[datetime.datetime]) -> list[tuple[datetime.datetime, dict]]:
    rs = []
    for dt in dts:
        str_data = dt.strftime(
            "{i:'-1',iteminfo:'^-1!FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF!FY3D!L1!img!1!s9000.dmz.nsmc.org.cn!IMG_LIB/FY3D/FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF/%Y%m%d/FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF.jpg'}"
        )
        rs.append(grequests.post(
            url="https://satellite.nsmc.org.cn/PortalSite/WebServ/ProductService.asmx/ShowInfo",
            data=str_data,
            headers={
                "Content-Type": "application/json;charset=utf-8",
            },
            timeout=5,
        ))
    responses = []
    timeout_count = 0
    for i, resp in tqdm(
            grequests.imap_enumerated(rs, size=1000),
            total=len(rs),
            desc="Requesting imagery info from NSMC website"
    ):
        if resp is None:  # Timeout
            timeout_count += 1
            continue
        responses.append((
            dts[i],
            __parse_response_text(resp.text)
        ))
    print("Timeouts:", timeout_count)
    return responses


def __parse_response_text(text: str) -> dict:
    text = text.replace("\\r\\n    \\", "")
    text = text[13:-7]
    text = text.replace("\\r\\n", "")
    text = text.replace("\\", "")
    return json.loads(text)


def orders_list() -> dict:
    r = session.post(
        url="https://satellite.nsmc.org.cn/PortalSite/Ord/MyOrders.aspx/GetDisplayOrder",
        headers={
            "Content-Type": "application/json;charset=utf-8",
        },
    )
    s = r.json()["d"]
    s = re.sub('(\w+):', '"\g<1>":', s)
    s = s.replace("'", '"')
    print(s)
    print(s[30: 45])
    return json.loads(s)

# res = orders_list()
# print(res)