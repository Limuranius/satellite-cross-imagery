from __future__ import annotations

import datetime
import json
from dataclasses import dataclass

import requests
from tqdm import tqdm

from Info import Info


@dataclass
class MERSIInfo(Info):
    @classmethod
    def find_containing_point(
            cls,
            start: datetime.date,
            end: datetime.date,
            lon: float,
            lat: float) -> list[MERSIInfo]:
        import MERSI_database
        start = datetime.datetime.combine(start, datetime.datetime.min.time())
        end = datetime.datetime.combine(end, datetime.datetime.min.time())
        step = datetime.timedelta(minutes=5)
        dt = start
        result = []
        with tqdm(total=(end - start).total_seconds() // 300) as pbar:
            while dt <= end:
                if MERSI_database.has_dt(dt):
                    info = MERSI_database.get_by_dt(dt)
                elif MERSI_database.has_invalid(dt):
                    pbar.update(1)
                    dt += step
                    continue
                else:
                    info = cls.from_datetime(dt)
                    if info is None:
                        print("Bruh", dt)
                        MERSI_database.add_invalid(dt)
                        pbar.update(1)
                        dt += step
                        continue
                    MERSI_database.add_info(info)
                if info.contains_pos(lon, lat):
                    result.append(info)
                pbar.update(1)
                dt += step
        return result

    @classmethod
    def from_datetime(cls, dt: datetime) -> MERSIInfo | None:
        str_data = dt.strftime(
            "{i:'-1',iteminfo:'^-1!FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF!FY3D!L1!img!1!s9000.dmz.nsmc.org.cn!IMG_LIB/FY3D/FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF/%Y%m%d/FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF.jpg'}")
        r = requests.post(
            "https://satellite.nsmc.org.cn/PortalSite/WebServ/ProductService.asmx/ShowInfo",
            data=str_data,
            headers={
                "Content-Type": "application/json;charset=utf-8",
            }
        )
        t = r.text
        t = t.replace("\\r\\n    \\", "")
        t = t[13:-7]
        t = t.replace("\\r\\n", "")
        t = t.replace("\\", "")
        t = json.loads(t)
        if int(t["datasize"]) == 0:
            return None
        return MERSIInfo(
            p1=(float(t["longitudewn"]), float(t["latitudewn"])),
            p2=(float(t["longitudeen"]), float(t["latitudeen"])),
            p3=(float(t["longitudees"]), float(t["latitudees"])),
            p4=(float(t["longitudews"]), float(t["latitudews"])),
            dt=dt,
            satellite="FY-3D",
            filename=t["archivename"],
        )
