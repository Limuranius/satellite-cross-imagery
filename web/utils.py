import ftplib
import os.path

import requests
from tqdm import tqdm


def download_file(
        url: str,
        output_path: str,
        session: requests.Session = None,
) -> None:
    # Streaming, so we can iterate over the response.
    if session is None:
        response = requests.get(url, stream=True)
    else:
        response = session.get(url, stream=True)

    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024

    with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
        with open(output_path, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

    if total_size != 0 and progress_bar.n != total_size:
        raise RuntimeError("Could not download file")


def download_ftp(
        url: str,
        login: str,
        password: str,
        output_dir: str,
):
    ftp = ftplib.FTP(url)
    ftp.login(login, password)

    files = ftp.nlst()
    wd = ftp.pwd()
    os.makedirs(output_dir, exist_ok=True)

    pbar = tqdm(unit="B", unit_scale=True)

    for filename in files:
        file = open(os.path.join(output_dir, filename), "wb")

        def callback(data):
            file.write(data)
            pbar.update(len(data))

        ftp.retrbinary("RETR " + os.path.join(wd, filename), callback)

        file.close()

    pbar.close()


def parse_ftp_url(url: str) -> tuple[str, str, str]:
    """Example: ftp://A202410110283035887:mi2_B47K@ftp.nsmc.org.cn"""
    url = url.lstrip("ftp://")
    url = url.replace(":", "ඞ", 1)
    url = url.replace("@", "ඞ", 1)
    url = url.replace("/", "ඞ", 1)
    login, password, url = url.split("ඞ")
    return url, login, password
