import pandas as pd


columns = ["wavelength", "srf"]


def load_mersi(band: int):
    file_path = f"MERSI SRF/FY3D_MERSI_SRF_CH{band:02d}_Pub.txt"
    with open(file_path) as file:
        lines = file.read().split("\n")[:-1]
        lines = [line.split() for line in lines]
        lines = [(float(line[0]), float(line[1])) for line in lines]
        return pd.DataFrame(lines, columns=columns)


def load_modis(band: int):
    file_path = f"MODIS SRF/{band}.txt"
    df = pd.read_csv(file_path)[["Wavelength", "RSR"]]
    df = df.rename(columns={"Wavelength": columns[0], "RSR": columns[1]})
    df = df.sort_values(by="wavelength")
    return df
