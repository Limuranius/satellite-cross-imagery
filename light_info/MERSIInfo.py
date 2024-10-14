from __future__ import annotations

import datetime
import json
from dataclasses import dataclass

import grequests
from tqdm import tqdm

from .Info import Info


@dataclass
class MERSIInfo(Info):
    @staticmethod
    def find_containing_point(
            start: datetime.date,
            end: datetime.date,
            lon: float,
            lat: float) -> list[MERSIInfo]:
        from . import MERSI_database
        start = datetime.datetime.combine(start, datetime.datetime.min.time())
        end = datetime.datetime.combine(end, datetime.datetime.min.time())
        step = datetime.timedelta(minutes=5)
        dt = start
        result = []
        dts_need_requesting = []

        # Looking for previously ordered infos in database
        while dt <= end:
            if MERSI_database.has_dt(dt):
                info = MERSI_database.get_by_dt(dt)
                result.append(info)
            elif MERSI_database.has_invalid(dt):
                pass
            else:
                dts_need_requesting.append(dt)
            dt += step

        # Requesting from NSMC infos that are not in database
        requested_infos = MERSIInfo.request_dts(dts_need_requesting)
        valid_infos = []
        for info in requested_infos:
            if info is None:
                MERSI_database.add_invalid(dt)
            else:
                valid_infos.append(info)
                result.append(info)
        MERSI_database.add_batch(valid_infos)

        # Got infos within given time interval. Now filtering ones that contain point inside them
        result = [info for info in result if info.contains_pos(lon, lat)]

        return result

    @staticmethod
    def __parse_response_text(text: str, dt: datetime.datetime) -> MERSIInfo | None:
        text = text.replace("\\r\\n    \\", "")
        text = text[13:-7]
        text = text.replace("\\r\\n", "")
        text = text.replace("\\", "")
        text = json.loads(text)
        if int(text["datasize"]) == 0:
            return None
        return MERSIInfo(
            p1=(float(text["longitudewn"]), float(text["latitudewn"])),
            p2=(float(text["longitudeen"]), float(text["latitudeen"])),
            p3=(float(text["longitudees"]), float(text["latitudees"])),
            p4=(float(text["longitudews"]), float(text["latitudews"])),
            dt=dt,
            satellite="FY-3D",
            filename=text["archivename"],
        )

    @staticmethod
    def request_dts(dts: list[datetime.datetime]) -> list[MERSIInfo | None]:
        rs = []
        for dt in dts:
            str_data = dt.strftime(
                "{i:'-1',iteminfo:'^-1!FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF!FY3D!L1!img!1!s9000.dmz.nsmc.org.cn!IMG_LIB/FY3D/FY3D_MERSI_GBAL_L1_YYYYMMDD_HHmm_1000M_MS.HDF/%Y%m%d/FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF.jpg'}")
            rs.append(grequests.post(
                url="https://satellite.nsmc.org.cn/PortalSite/WebServ/ProductService.asmx/ShowInfo",
                data=str_data,
                headers={
                    "Content-Type": "application/json;charset=utf-8",
                },
                timeout=5,
            ))
        responses = []
        for i, resp in tqdm(
                grequests.imap_enumerated(rs, size=100),
                total=len(rs),
                desc="Requesting imagery info from NSMC website"
        ):
            if resp is None:
                continue
            info = MERSIInfo.__parse_response_text(resp.text, dts[i])
            responses.append(info)
        return responses
