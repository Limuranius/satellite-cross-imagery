import requests
import pandas as pd
from tqdm import trange

url_fmt = "https://calval.jpl.nasa.gov/downloads/modis_srfs/ModisAquaBand{band:02d}SrfData.txt"

for band in trange(1, 37):
    text = requests.get(
        url_fmt.format(band=band)
    ).text
    lines = text.split("\n")
    lines = lines[10:-1]
    lines = [line.split() for line in lines]
    lines = [(int(line[0]), int(line[1]), float(line[2]), float(line[3])) for line in lines]
    df = pd.DataFrame(
        data=lines,
        columns=["Band", "Channel", "Wavelength", "RSR"]
    )
    df.to_csv(f"MODIS SRF/{band}.txt", index=False)