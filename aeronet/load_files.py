import os
from io import StringIO
import pandas as pd
from tqdm import tqdm

with open("needed_sites.txt") as f:
    NEEDED_SITES = f.read().split()
    NEEDED_SITES = list(map(lambda s: s.lower(), NEEDED_SITES))


def aeronet_file_to_df(file_path: str) -> pd.DataFrame:
    with open(file_path) as f:
        for _ in range(6):
            f.readline()

        data = StringIO(f.read())
        return pd.read_csv(data)


def load_no_phase(dir_path: str) -> pd.DataFrame:
    files = os.listdir(dir_path)

    def filt(file_name: str):
        site = file_name[18:-4].lower()
        return site in NEEDED_SITES

    files = list(filter(filt, files))
    files = [os.path.join(dir_path, file) for file in files]

    dfs = []
    for file in tqdm(files, desc="Loading aerosol inversion (no phase functions)..."):
        dfs.append(aeronet_file_to_df(file))
    data = pd.concat(dfs)
    data["Datetime"] = pd.to_datetime(
        data["Date(dd:mm:yyyy)"] + " " + data["Time(hh:mm:ss)"],
        format="%d:%m:%Y %H:%M:%S"
    )
    return data


def load_phase(dir_path: str) -> pd.DataFrame:
    files = os.listdir(dir_path)

    def filt(file_name: str):
        site = file_name[18:-4].lower()
        return site in NEEDED_SITES

    files = list(filter(filt, files))
    files = [os.path.join(dir_path, file) for file in files]

    dfs = []
    for file in tqdm(files, desc="Loading aerosol phase functions files..."):
        dfs.append(aeronet_file_to_df(file))
    data = pd.concat(dfs)
    data["Datetime"] = pd.to_datetime(
        data["Date(dd:mm:yyyy)"] + " " + data["Time(hh:mm:ss)"],
        format="%d:%m:%Y %H:%M:%S"
    )
    return data


def load_ocean_color(dir_path: str) -> pd.DataFrame:
    files = os.listdir(dir_path)
    sites = [file_name[18:-10] for file_name in files]
    files = [os.path.join(dir_path, file) for file in files]
    dfs = []
    for file, site in tqdm(
            zip(files, sites),
            desc="Loading ocean color files...",
            total=len(files)
    ):
        df = aeronet_file_to_df(file)
        df["Site"] = [site] * len(df)
        dfs.append(df)
    data = pd.concat(dfs)
    data["Datetime"] = pd.to_datetime(
        data["Date(dd-mm-yyyy)"] + " " + data["Time(hh:mm:ss)"],
        format="%d:%m:%Y %H:%M:%S"
    )
    return data
