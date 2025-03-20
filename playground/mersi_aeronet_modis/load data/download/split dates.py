import datetime
import itertools

from light_info.MERSIInfo import MERSIInfo

EACH_DATE_MB = 300
MAX_CART_MB = 5000
IMGS_PER_CART = MAX_CART_MB // EACH_DATE_MB

with open("need_download.txt", "r") as file:
    dts = [datetime.datetime.fromisoformat(s) for s in file.read().strip().split("\n")]
    infos = MERSIInfo.from_dts(dts)
groups = [dts[i: i + IMGS_PER_CART] for i in range(0, len(infos), IMGS_PER_CART)]
print(groups)

with open("groups.txt", "w") as file:
    for group in groups:
        print(*group, sep="\n", file=file, end="\n\n\n")