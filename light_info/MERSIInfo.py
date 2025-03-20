from __future__ import annotations

import datetime
from dataclasses import dataclass

import numpy as np

import web.NSMC_parser
from custom_types import LonLat
from .Info import Info


@dataclass
class MERSIInfo(Info):
    @staticmethod
    def find(
            start: datetime.datetime,
            end: datetime.datetime,
            point: LonLat = None
    ) -> list[Info]:
        from . import MERSI_database
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
            if isinstance(info, datetime.datetime):
                MERSI_database.add_invalid(info)
            else:
                valid_infos.append(info)
                result.append(info)
        MERSI_database.add_batch(valid_infos)

        # Got infos within given time interval. Now filtering ones that contain point inside them
        if point:
            lon, lat = point
            result = [info for info in result if info.contains_pos(lon, lat)]

        return result

    @staticmethod
    def from_dts(dts: list[datetime.datetime]) -> list[Info]:
        from . import MERSI_database
        return [MERSI_database.get_by_dt(dt) for dt in dts]

    @staticmethod
    def request_dts(dts: list[datetime.datetime]) -> list[MERSIInfo | datetime.datetime]:
        responses = web.NSMC_parser.request_dts_infos(dts)
        result = []
        for dt, data in responses:
            if int(data["datasize"]) == 0:
                result.append(dt)
                continue
            result.append(MERSIInfo(
                p1=(float(data["longitudewn"]), float(data["latitudewn"])),
                p2=(float(data["longitudeen"]), float(data["latitudeen"])),
                p3=(float(data["longitudees"]), float(data["latitudees"])),
                p4=(float(data["longitudews"]), float(data["latitudews"])),
                dt=dt,
                satellite="FY-3D",
                filename=data["archivename"],
            ))
        return result

    def get_preview(self) -> np.ndarray:
        return web.NSMC_parser.get_preview(self.dt)
