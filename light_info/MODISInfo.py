from __future__ import annotations

import datetime as dt
import itertools
from dataclasses import dataclass, field

import requests

from .Info import Info


@dataclass
class MODISInfo(Info):
    fileURL: str

    geo_filename: str
    geo_file_url: str

    cloud_mask_filename: str
    cloud_mask_file_url: str

    @staticmethod
    def find_containing_point(
            start: dt.date,
            end: dt.date,
            lon: float,
            lat: float) -> list[MODISInfo]:
        img_infos = find_inside_area(start, end, lon, lat, lon + 0.1, lat + 0.1)
        img_infos = [info for info in img_infos if info.contains_pos(lon, lat)]
        return img_infos

    def get_file_url(self) -> str:
        return "https://ladsweb.modaps.eosdis.nasa.gov" + self.fileURL

    def get_geo_file_url(self) -> str:
        return "https://ladsweb.modaps.eosdis.nasa.gov" + self.geo_file_url

    def get_cloud_mask_file_url(self) -> str:
        return "https://ladsweb.modaps.eosdis.nasa.gov" + self.cloud_mask_file_url


def find_inside_area(
        start: dt.date,
        end: dt.date,
        w: float,
        n: float,
        e: float,
        s: float,
) -> list[MODISInfo]:
    url = ("https://ladsweb.modaps.eosdis.nasa.gov/api/v1/files/product=MYD021KM&collection=61"
           f"&dateRanges={start.isoformat()}..{end.isoformat()}"
           f"&areaOfInterest=x{w}y{n},x{e}y{s}"
           "&dayCoverage=true"
           "&dnboundCoverage=true")
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
