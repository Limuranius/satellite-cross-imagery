from __future__ import annotations

import datetime
import json

import requests

from Info import Info


class MERSIInfo(Info):
    @classmethod
    def find_containing_point(
            cls,
            start: datetime.date,
            end: datetime.date,
            lon: float,
            lat: float) -> list[MERSIInfo]:
        pass


    @classmethod
    @classmethod
    def from_datetime(cls, dt: datetime) -> MERSIInfo:
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
        return MersiImageInfo(
            dt=dt,
            Satellite=t["satellitename"],
            File=t["archivename"],
            Product=t["PRODUCTIONNAMEENG"],
            Receiving_station_identification=t["station"],
            Data_collection_start_time_UTC=datetime.fromisoformat(t["databegindate"]),
            Data_collection_end_time_UTC=datetime.fromisoformat(t["dataenddate"]),
            Data_generation_time=datetime.fromisoformat(t["datacreatedate"]),
            Data_Size=int(t["datasize"]),
            Quality_Evaluation_logo=int(t["qualityflag"]),
            Total_number_of_scan_lines=int(t["actualscanline"]),
            Actual_number_of_scan_lines=int(t["actualscanline"]),
            Southeast_corner_latitude=float(t["latitudees"]),
            Northwest_corner_latitude=float(t["latitudewn"]),
            Southwest_corner_Latitude=float(t["latitudews"]),
            Northeast_corner_latitude=float(t["latitudeen"]),
            Northeast_corner_longitude=float(t["longitudeen"]),
            Southeast_corner_longitude=float(t["longitudees"]),
            Northwest_corner_longitude=float(t["longitudewn"]),
            Southwest_corner_longitude=float(t["longitudews"]),
        )