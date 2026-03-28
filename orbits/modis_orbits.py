import bisect

import numpy as np

import paths
from pyorbital.orbital import Orbital

tles = open(paths.DATA_DIR / "MODIS AQUA TLEs 2002-2025.txt").readlines()
tles = [(tles[i + 1].strip(), tles[i + 2].strip()) for i in range(0, len(tles), 3)]
orbs = [Orbital("AQUA", line1=tle[0], line2=tle[1]) for tle in tles]


def get_orbital(utc_time):
    utc_time = np.datetime64(utc_time)
    orb = orbs[
        min(bisect.bisect_left(
            orbs,
            utc_time,
            key=lambda orb: orb.tle.epoch
        ), len(orbs) - 1)
    ]
    diff = abs(orb.tle.epoch - utc_time).astype('timedelta64[h]')
    # print("Time difference with TLE:", diff)
    return orb
