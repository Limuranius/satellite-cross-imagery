import datetime
import math

from web import NSMC_parser
from processing.MERSIImage import MERSIImage


downloaded_dts = MERSIImage.all_dts()
download_list = [datetime.datetime.fromisoformat(s.strip()) for s in open("need_download.txt")]

need_download_dts = sorted(set(download_list) - set(downloaded_dts))
print(f"Need to download {len(need_download_dts)} dates")

storage_info = NSMC_parser.get_order_size()
remain_space = storage_info["maxfiledownloadcount"] - storage_info["sizeOfOrdAndShop"]

# Все файлы весят одинаково, так что просто расчитываем кол-во, которое нам надо заказать
# l1_size = NSMC_parser.get_metadata(need_download_dts[0], NSMC_parser.DataType.L1)["DATASIZE"]
l1_size = 197
# l1_geo_size = NSMC_parser.get_metadata(need_download_dts[0], NSMC_parser.DataType.L1_GEO)["DATASIZE"]
l1_geo_size = 78.1
size = l1_size + l1_geo_size
to_order_count = math.floor(remain_space / size)

need_download_dts = need_download_dts[2 * to_order_count:]

print(f"Can order {to_order_count} L1 and L1_GEO pairs")
NSMC_parser.select_dts(need_download_dts[:to_order_count], NSMC_parser.DataType.L1)
NSMC_parser.select_dts(need_download_dts[:to_order_count], NSMC_parser.DataType.L1_GEO)

print("Done. Now go to shopping cart: https://satellite.nsmc.org.cn/dataportal/en/data/cart.html")