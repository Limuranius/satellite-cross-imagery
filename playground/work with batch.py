from datetime import timedelta

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from processing import matching
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.matching import load_matching_pixels
from processing.preprocessing import group_by_time

groups = group_by_time(timedelta(minutes=30))
# [4, 5, 7, 8, 9]
groups = [group[1] for group in enumerate(groups) if group[0] in [0, 1, 2, 3, 6, 10]]
# print(*groups, sep="\n")


dfs = []

for mersi_paths, modis_paths in groups:
    img_mersi = MERSIImage(
        mersi_paths[0],
        mersi_paths[1],
        "8",
    )

    img_modis = MODISImage(
        modis_paths[0],
        modis_paths[1],
        "8",
    )
    img_modis.load_cloud_mask(modis_paths[2])

    pixels = load_matching_pixels(img_mersi, img_modis, force_recalculate=True)
    df = matching.matching_stats(img_mersi, img_modis, pixels)
    df["year"] = img_mersi.dt.year
    dfs.append(df)

all_years_df = pd.concat(dfs)

sns.histplot(
    data=all_years_df,
    x=all_years_df["mersi_rad"] / all_years_df["modis_rad"],
    hue="year",
    palette="tab10",
    stat="proportion",
    common_norm=False,
)
plt.show()

# sns.relplot(
#     all_years_df,
#     x="mersi_solz",
#     y="mersi_rad",
#     hue="year",
#     s=1,
# )
# plt.show()

sns.relplot(
    all_years_df,
    x="mersi_rad",
    y="modis_rad",
    hue="year",
    s=1,
    palette="tab10"
)
plt.show()

# sns.relplot(
#     all_years_df,
#     x=range(len(all_years_df)),
#     y="rad_diff",
#     hue="year",
# )
