from web.web_utils import parse_ftp_url, download_ftp
import paths
import os
import shutil

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

ftp_urls = [
    "ftp://A202504150024003655:N7MfFcW_@ftp.nsmc.org.cn",
    "ftp://A202504150024003736:fN4J_7gL@ftp.nsmc.org.cn",
    "ftp://A202504150024003818:n_q0FCmT@ftp.nsmc.org.cn",
    "ftp://A202504150024003985:JX6_lw3j@ftp.nsmc.org.cn",
    "ftp://A202504140005002262:_82GEBbD@ftp.nsmc.org.cn",
    "ftp://A202504140005002323:IagCe2_b@ftp.nsmc.org.cn",
    "ftp://A202504140005002594:4o7t_Gnh@ftp.nsmc.org.cn",
    "ftp://A202504140005002437:V7jL7H_C@ftp.nsmc.org.cn",
    "ftp://A202504130811037129:41C2yB_v@ftp.nsmc.org.cn",
    "ftp://A202504130811037011:jH_5nI42@ftp.nsmc.org.cn",
    "ftp://A202504130811037259:T_trLQ28@ftp.nsmc.org.cn",
]


for ftp_url in ftp_urls:
    url, login, password = parse_ftp_url(ftp_url)
    download_ftp(url, login, password, DOWNLOADS_DIR)

# Distributing files to folders
for file in os.listdir(DOWNLOADS_DIR):
    src = os.path.join(DOWNLOADS_DIR, file)
    if "1000M" in file:
        dst = os.path.join(paths.MERSI_L1_DIR, file)
        shutil.move(src, dst)
    elif "GEO1K" in file:
        dst = os.path.join(paths.MERSI_L1_GEO_DIR, file)
        shutil.move(src, dst)