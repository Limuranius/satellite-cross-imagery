import datetime
import json

import requests

session = requests.Session()
cookies_str = input("Enter cookies from https://satellite.nsmc.org.cn: ")
for pair in cookies_str.split("; "):
    key, value = pair.split("=", maxsplit=1)
    session.cookies.set(key, value)


def select_dt(dt: datetime.datetime) -> None:
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Content-Length": "114",
        "Content-Type": "application/json;charset=utf-8",
        "Host": "satellite.nsmc.org.cn",
        "Origin": "https://satellite.nsmc.org.cn",
        "Priority": "u=0",
        "Referer": "https://satellite.nsmc.org.cn/PortalSite/Data/FileShow.aspx",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    filename_fmt = "FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF"
    post_data = {
        "filename": dt.strftime(filename_fmt),
        "ischecked": True,
        "satellitecode": "FY3D",
        "datalevel": "L1"
    }

    r = session.post(
        "https://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/selectOne",
        headers=headers,
        data=json.dumps(post_data)
    )