from __future__ import annotations

import datetime
from dataclasses import dataclass

import requests

from Info import Info


@dataclass
class MODISInfo(Info):
    fileURL: str = None

    @classmethod
    def find_containing_point(
            cls,
            start: datetime.date,
            end: datetime.date,
            lon: float,
            lat: float) -> list[MODISInfo]:
        img_infos = find_inside_area(start, end, lon, lat, lon + 0.1, lat + 0.1)
        img_infos = [info for info in img_infos if info.contains_pos(lon, lat)]
        return img_infos


def find_inside_area(
        start: datetime.date,
        end: datetime.date,
        w: float,
        n: float,
        e: float,
        s: float,
) -> list[MODISInfo]:
    url_fmt = ("https://ladsweb.modaps.eosdis.nasa.gov/api/v1/files/product=MYD021KM&collection=61"
               f"&dateRanges={start.isoformat()}..{end.isoformat()}"
               f"&areaOfInterest=x{w}y{n},x{e}y{s}"
               "&dayCoverage=true"
               "&dnboundCoverage=true")

    r = requests.get(url_fmt)

    result = []
    for r in r.json().values():
        result.append(MODISInfo(
            p1=(float(r["GRingLongitude1"]), float(r["GRingLatitude1"])),
            p2=(float(r["GRingLongitude2"]), float(r["GRingLatitude2"])),
            p3=(float(r["GRingLongitude3"]), float(r["GRingLatitude3"])),
            p4=(float(r["GRingLongitude4"]), float(r["GRingLatitude4"])),
            dt=datetime.datetime.fromisoformat(r["start"]),
            satellite="MODIS AQUA",
            filename=r["name"],
            fileURL=r["fileURL"]
        ))
    return result
