import csv
import datetime as dt
import itertools
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

from custom_types import LonLat
from light_info.MODISInfo import MODISInfo

CSV_PATH = "/home/gleb123/satellite-cross-imagery/light_info/modis_data.csv"


def request_between_dates(
        start: dt.date,
        end: dt.date,
) -> list[MODISInfo]:
    url = ("https://ladsweb.modaps.eosdis.nasa.gov/api/v1/files/product=MYD021KM&collection=61"
           f"&dateRanges={start.isoformat()}..{end.isoformat()}"
           "&dayCoverage=true"
           )
    geo_url = url.replace("MYD021KM", "MYD03")
    cloud_mask_url = url.replace("MYD021KM", "MYD35_L2")

    r_l1b = requests.get(url)
    r_geo = requests.get(geo_url)
    r_cloud_mask = requests.get(cloud_mask_url)

    json_l1b = r_l1b.json()
    json_geo = r_geo.json()
    json_cloud_mask = r_cloud_mask.json()

    items_l1b = list(json_l1b.values())
    items_geo = list(json_geo.values())
    items_cloud_mask = list(json_cloud_mask.values())

    items = items_l1b + items_geo + items_cloud_mask
    items = sorted(items, key=lambda x: dt.datetime.fromisoformat(x["start"]))
    groups = itertools.groupby(
        items,
        key=lambda x: x["start"],
    )
    result = []
    for info_dt, group in groups:
        group = list(group)
        if len(group) != 3:
            continue
        img_info, geo_info, cloud_mask_info = group
        assert dt.datetime.fromisoformat(img_info["start"]) == dt.datetime.fromisoformat(
            geo_info["start"]) == dt.datetime.fromisoformat(cloud_mask_info["start"])
        result.append(MODISInfo(
            p1=(float(img_info["GRingLongitude1"]), float(img_info["GRingLatitude1"])),
            p2=(float(img_info["GRingLongitude2"]), float(img_info["GRingLatitude2"])),
            p3=(float(img_info["GRingLongitude3"]), float(img_info["GRingLatitude3"])),
            p4=(float(img_info["GRingLongitude4"]), float(img_info["GRingLatitude4"])),
            dt=dt.datetime.fromisoformat(img_info["start"]),
            satellite="MODIS AQUA",
            filename=img_info["name"],
            fileURL=img_info["fileURL"],
            geo_filename=geo_info["name"],
            geo_file_url=geo_info["fileURL"],
            cloud_mask_filename=cloud_mask_info["name"],
            cloud_mask_file_url=cloud_mask_info["fileURL"]
        ))
    return result


def to_line(info: MODISInfo):
    return [
        info.p1[0], info.p1[1],
        info.p2[0], info.p2[1],
        info.p3[0], info.p3[1],
        info.p4[0], info.p4[1],
        info.dt.isoformat(),
        info.filename,
        info.fileURL,
        info.geo_filename,
        info.geo_file_url,
        info.cloud_mask_filename,
        info.cloud_mask_file_url,
    ]


def parse_line(line) -> MODISInfo:
    return MODISInfo(
        (float(line[0]), float(line[1])),
        (float(line[2]), float(line[3])),
        (float(line[4]), float(line[5])),
        (float(line[6]), float(line[7])),
        dt.datetime.fromisoformat(line[8]),
        "MODIS AQUA",
        line[9],
        line[10],
        line[11],
        line[12],
        line[13],
        line[14],
    )


def collect_data(
        start: dt.date,
        end: dt.date,
):
    total = (end.year * 12 + end.month) - (start.year * 12 + start.month)
    pbar = tqdm(total=total, desc="collecting MODIS data")
    t = start
    result = []
    while t < end:
        t_next = t + relativedelta(months=1)
        result += request_between_dates(t, t_next)
        t = t_next
        pbar.update(1)

    # Removing dates that already have been ordered
    with open(CSV_PATH) as csvfile:
        reader = csv.reader(csvfile)
        previous_data = [*reader]
        existing_dates = set([dt.datetime.fromisoformat(line[8]) for line in previous_data])
    result = [info for info in result if info.dt not in existing_dates]

    lines = previous_data + [to_line(info) for info in result]
    with open(CSV_PATH, "w", newline="") as file:
        csv.writer(file).writerows(lines)

    return result


def load_data(
        start: dt.date,
        end: dt.date,
        point: LonLat = None,
) -> list[MODISInfo]:
    result = []
    with open(CSV_PATH) as csvfile:
        reader = csv.reader(csvfile)
        data = [*reader]
        for line in data:
            info = parse_line(line)
            is_good = start <= info.dt <= end
            if point:
                lon, lat = point
                is_good = is_good and info.contains_pos(lon, lat)
            if is_good:
                result.append(info)
    return result


def load_dts(dts: list[datetime]) -> list[MODISInfo]:
    result = []
    with open(CSV_PATH) as csvfile:
        reader = csv.reader(csvfile)
        data = [*reader]
        for line in data:
            info = parse_line(line)
            if info.dt in dts:
                result.append(info)
    return result
