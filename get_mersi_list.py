from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from datetime import datetime

import requests
from tqdm import tqdm

import database
from Info import Info


@dataclass(frozen=True)
class MersiImageInfo:
    dt: datetime
    Satellite: str
    File: str
    Product: str
    Receiving_station_identification: str
    Data_collection_start_time_UTC: datetime
    Data_collection_end_time_UTC: datetime
    Data_generation_time: datetime
    Data_Size: int
    Quality_Evaluation_logo: int
    Total_number_of_scan_lines: int
    Actual_number_of_scan_lines: int
    Northeast_corner_latitude: float
    Northeast_corner_longitude: float
    Southeast_corner_latitude: float
    Southeast_corner_longitude: float
    Northwest_corner_latitude: float
    Northwest_corner_longitude: float
    Southwest_corner_Latitude: float
    Southwest_corner_longitude: float




def find_containing_point(
        start: datetime.date,
        end: datetime.date,
        lon: float,
        lat: float,
) -> list[Info]:
    start = datetime.datetime.combine(start, datetime.datetime.min.time())
    end = datetime.datetime.combine(end, datetime.datetime.min.time())
    step = datetime.timedelta(minutes=5)
    dt = start
    result = []
    with tqdm(total=(end - start).total_seconds() // 300) as pbar:
        while dt <= end:
            if database.has_dt(dt):
                info = database.get_by_dt(dt)
            elif database.has_invalid(dt):
                pbar.update(1)
                dt += step
                continue
            else:
                info = MersiImageInfo.from_datetime(dt)
                if info is None:
                    print("Bruh", dt)
                    database.add_invalid(dt)
                    pbar.update(1)
                    dt += step
                    continue
                info = Info(
                    p1=(info.Northwest_corner_longitude, info.Northwest_corner_latitude),
                    p2=(info.Northeast_corner_longitude, info.Northeast_corner_latitude),
                    p3=(info.Southeast_corner_longitude, info.Southeast_corner_latitude),
                    p4=(info.Southwest_corner_longitude, info.Southwest_corner_Latitude),
                    dt=dt,
                    satellite="FY-3D",
                    filename=info.File,
                )
                database.add_info(info)
            if info.contains_pos(lon, lat):
                result.append(info)
            pbar.update(1)
            dt += step
    return result
