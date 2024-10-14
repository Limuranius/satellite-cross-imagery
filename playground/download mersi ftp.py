from web.utils import parse_ftp_url, download_ftp
import paths
import os
import shutil

DOWNLOADS_DIR = "downloads"

# # Downloading files
# ftp_url = input("Enter FTP url: ")
# url, login, password = parse_ftp_url("ftp://A202410140463397041:hHS_5BCS@ftp.nsmc.org.cn")
# download_ftp(url, login, password, DOWNLOADS_DIR)

# Distributing files to folders
for file in os.listdir(DOWNLOADS_DIR):
    src = os.path.join(DOWNLOADS_DIR, file)
    if "1000M" in file:
        dst = os.path.join(paths.MERSI_L1_DIR, file)
        shutil.move(src, dst)
    elif "GEO1K" in file:
        dst = os.path.join(paths.MERSI_L1_GEO_DIR, file)
        shutil.move(src, dst)