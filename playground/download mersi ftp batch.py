from web.utils import parse_ftp_url, download_ftp
import paths
import os
import shutil

DOWNLOADS_DIR = "/media/gleb123/data/downloads"

ftp_urls = [
    # "ftp://A202412190043139178:bf_vVER0@ftp.nsmc.org.cn",
    # "ftp://A202412190595055516:h_OoblC3@ftp.nsmc.org.cn",
    # "ftp://A202412190053756474:XK4g_7OQ@ftp.nsmc.org.cn",
    # "ftp://A202412190134808022:5MuX3RF_@ftp.nsmc.org.cn",
    # "ftp://A202412190007434437:J_nTCU2t@ftp.nsmc.org.cn",
    # "ftp://A202412190297593242:PN4Yw9a_@ftp.nsmc.org.cn",

    "ftp://A202412200504641476:i69v_Q6Z@ftp.nsmc.org.cn",
    "ftp://A202412200004513868:5_Nszo8D@ftp.nsmc.org.cn",
    "ftp://A202412200037029597:Y_TddWZ9@ftp.nsmc.org.cn",
    "ftp://A202412200525865101:V8qm_zaT@ftp.nsmc.org.cn",
    "ftp://A202412200279638754:X_YOo_f9@ftp.nsmc.org.cn",
    "ftp://A202412200266184207:BM3YjKt_@ftp.nsmc.org.cn",
]

for ftp_url in ftp_urls:
    url, login, password = parse_ftp_url(ftp_url)
    download_ftp(url, login, password, DOWNLOADS_DIR)