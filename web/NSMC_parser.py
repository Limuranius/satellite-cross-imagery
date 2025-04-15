import datetime
import enum
from io import BytesIO

import grequests
import numpy as np
import requests
from PIL import Image
from tqdm import tqdm

import paths

cookie = None


def require_cookie(func):
    def wrapped(*args, **kwargs):
        global cookie
        if cookie is None:
            cookie = input("Enter cookies from https://satellite.nsmc.org.cn: ")
        return func(*args, **kwargs)

    return wrapped


class DataType(enum.Enum):
    L1 = enum.auto()
    L1_GEO = enum.auto()
    CLOUD_MASK = enum.auto()

    def suffix(self) -> str:
        return {
            DataType.L1: "1000M",
            DataType.L1_GEO: "GEO1K",
        }[self]

    def output_dir(self) -> str:
        return {
            DataType.L1: paths.MERSI_L1_DIR,
            DataType.L1_GEO: paths.MERSI_L1_GEO_DIR,
        }[self]

    def get_filename(self, dt: datetime.datetime) -> str:
        if self in [DataType.L1, DataType.L1_GEO]:
            filename_fmt = f"FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_{self.suffix()}_MS.HDF"
        elif self == DataType.CLOUD_MASK:
            filename_fmt = "FY3D_MERSI_ORBT_L2_CLM_MLT_NUL_%Y%m%d_%H%M_1000M_MS.HDF"
        return dt.strftime(filename_fmt)

    def get_production_code(self) -> str:
        return {
            DataType.L1: "FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF",
            DataType.L1_GEO: "FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_GEO1K_MS.HDF",
        }[self]


def get_metadata(
        dt: datetime.datetime,
        data_type: DataType,
) -> dict:
    resp = requests.post(
        "https://data.nsmc.org.cn/DataPortal/v1/data/selection/product/file/metadata",
        data={
            "fileName": data_type.get_filename(dt),
            "productionCode": data_type.get_production_code(),
        }
    ).json()["resource"]
    resp["DATASIZE"] /= 1024 * 1024  # Переводим в MB
    return resp


def get_many_metadatas(
        dts: list[datetime.datetime],
        data_type: DataType = DataType.L1,
) -> list[tuple[datetime.datetime, dict]]:
    rs = []
    for dt in dts:
        rs.append(grequests.post(
            url="https://data.nsmc.org.cn/DataPortal/v1/data/selection/product/file/metadata",
            data={
                "fileName": data_type.get_filename(dt),
                "productionCode": data_type.get_production_code(),
            },
            # timeout=5,
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
            resp.json()
        ))
    print("Timeouts:", timeout_count)
    return responses


@require_cookie
def select_dts(
        dts: list[datetime.datetime],
        data_type: DataType,
) -> None:
    file_names = [data_type.get_filename(dt) for dt in dts]
    r = requests.post(
        "https://data.nsmc.org.cn/DataPortal/v1/data/cart/subbatch?from=portalEn",
        json=file_names,
        headers={"Cookie": cookie}
    )


def select_dt(
        dt: datetime.datetime,
        data_type: DataType,
) -> None:
    select_dts([dt], data_type)


@require_cookie
def get_order_size():
    """
    sizeOfShop - size of current order (in MB)
    sizeOfOrd - size of previously ordered (in MB)
    sizeOfOrdAndShop - size of current order + previously ordered (in MB)
    maxfiledownloadcount - daily volume limit (in MB)
    """
    resp = requests.get(
        "https://data.nsmc.org.cn/DataPortal/v1/data/cart/subsize",
        headers={"Cookie": cookie}
    ).json()["resource"]
    resp["sizeOfShop"] /= 1024 * 1024
    resp["sizeOfOrd"] /= 1024 * 1024
    resp["sizeOfOrdAndShop"] /= 1024 * 1024
    return resp


def get_preview(dt: datetime.datetime) -> np.ndarray:
    url_fmt = "https://img.nsmc.org.cn/IMG_LIB/FY3D/FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF/%Y%m%d/FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF.jpg"
    image_url = dt.strftime(url_fmt)
    img_resp = requests.get(image_url)
    img = Image.open(BytesIO(img_resp.content))
    return np.array(img)


@require_cookie
def get_orders_list():
    return requests.get(
        "https://satellite.nsmc.org.cn/DataPortal/v1/data/order/suborder",
        headers={"Cookie": cookie}
    ).json()["resource"]


@require_cookie
def get_order_info(order_code: str):
    return requests.get(
        f"https://satellite.nsmc.org.cn/DataPortal/v1/data/order/{order_code}/url",
        headers={"Cookie": cookie},
    ).json()["resource"]


ord_list = get_orders_list()
for ord in ord_list:
    ord_code = ord["ordercode"]
    ord_info = get_order_info(ord_code)
    if "FTPACCOUNT" in ord_info:
        name = ord_info["FTPACCOUNT"]
        password = ord_info["FTPPASSWORD"]
        print(f"ftp://{name}:{password}@ftp.nsmc.org.cn")

# print(get_order_info("A202504130811037011"))


