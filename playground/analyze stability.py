import math
from datetime import datetime

import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt
import seaborn as sns

from processing import matching
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.load_imagery import iterate_close_images, iterate_mersi, iterate_modis, iterate_image_groups
from processing.matching import visualize_matching_pixels, load_matching_pixels
from processing.preprocessing import manual_group
from utils import datetime_range

from visuals.graphs import relplot_with_linregress
import visuals.map_2d

pairs = [
    ("8", "8"),
    # ("9", "9"),
    # ("10", "10"),
    # ("11", "12"),
    # ("12", "13lo"),
    # ("12", "14lo"),
]
interval = (
    datetime(2024, 9, 4, 14, 20),
    datetime(2024, 9, 5)
)

generate_iterator = lambda mersi_band, modis_band: iterate_image_groups(
    groups=manual_group(
        mersi_dts=list(datetime_range(
            datetime(2024, 9, 4, 14, 20),
            datetime(2024, 9, 4, 14, 55),
        )),
        modis_dts=list(datetime_range(
            datetime(2024, 9, 4, 14, 20),
            datetime(2024, 9, 4, 14, 55),
        )),
    ),
    mersi_band=mersi_band,
    modis_band=modis_band,
)


def iterate_images(func, mersi_band="8", modis_band="8", force_recalculate=False):
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(mersi_band, modis_band)):
        print(img_mersi.dt)
        print(img_modis.dt)
        pixels = load_matching_pixels(
            img_mersi, img_modis,
            force_recalculate=force_recalculate
        )
        func(img_mersi, img_modis, pixels)
        print(i)


def look_at_matching_pixels():
    MERSI_BAND = "10"
    MODIS_BAND = "10"
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
        # if i != 7:
        #     print(i)
        #     continue
        pixels = load_matching_pixels(
            img_mersi, img_modis,
        )
        visualize_matching_pixels(
            img_mersi,
            img_modis,
            pixels
        )
        # plt.show()
        plt.savefig(f"stability test/images/{i}.png")
        plt.close()
        print(i)


def georeference_stability(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    distances = []
    for mersi_coord, modis_coord in pixels:
        mersi_lon = img_mersi.longitude[*mersi_coord]
        mersi_lat = img_mersi.latitude[*mersi_coord]
        modis_lon = img_modis.longitude[*modis_coord]
        modis_lat = img_modis.latitude[*modis_coord]
        dist = math.sqrt((mersi_lon - modis_lon) ** 2 + (mersi_lat - modis_lat) ** 2)
        distances.append(dist)
    plt.hist(distances, bins=100)
    plt.show()


def recalculate_matching_pixels():
    for img_mersi, img_modis in tqdm.tqdm(generate_iterator("8", "8"), desc="Recalculating matching pixels"):
        pixels = load_matching_pixels(
            img_mersi, img_modis,
            force_recalculate=True
        )

        # visualize_matching_pixels(img_mersi, img_modis, pixels)
        # plt.show()


def save_stats():
    for MERSI_BAND, MODIS_BAND in pairs:
        print(MERSI_BAND, MODIS_BAND)
        dfs = []
        for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
            pixels = load_matching_pixels(img_mersi, img_modis)

            df = matching.matching_stats(img_mersi, img_modis, pixels)
            df["image_number"] = i
            dfs.append(df)

            print(i)

        total_df = pd.concat(dfs)
        file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
        total_df.to_pickle(file_path)


def process_stats():
    # writer = pd.ExcelWriter("stability test/results.xlsx")
    for MERSI_BAND, MODIS_BAND in pairs:
        file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
        df = pd.read_pickle(file_path)

        # sns.histplot(
        #     data=df,
        #     x=df["mersi_rad"] / df["modis_rad"],
        #     hue="image_number",
        #     palette="tab10",
        #     stat="proportion",
        #     common_norm=False,
        # )
        # plt.title(f"MERSI-2 band {MERSI_BAND}, MODIS band {MODIS_BAND}")
        # plt.xlabel("MERSI-2 radiance / MODIS radiance")
        # plt.show()

        sns.relplot(
            df,
            x="mersi_rad",
            y="modis_rad",
            hue="image_number",
            palette="tab10",
            s=2,
            edgecolor=None,
        )
        plt.show()

        # sns.histplot(
        #     data=df,
        #     x="mersi_rad",
        #     hue="image_number",
        #     palette="tab10",
        #     stat="proportion",
        #     common_norm=False,
        # )
        # plt.title(f"MERSI-2 band {MERSI_BAND} radiance")
        # plt.xlabel("MERSI-2 radiance")
        # plt.savefig(f"stability test/{MERSI_BAND}.png", dpi=300)
        # plt.close()

        # Номер снимка, mean, std, кол-во пикселей
        # sheet_data = [["Номер снимка", "mean", "std", "кол-во пикселей"]]
        # # img_datas = []
        # for img_i in range(8):
        #     img_data = df[df["image_number"] == img_i]
        #     rel = img_data["mersi_rad"] / img_data["modis_rad"]
        #     # img_datas.append(rel)
        #     sheet_data.append([
        #         img_i,
        #         rel.mean(),
        #         rel.std(),
        #         len(rel)
        #     ])

        # ttests = [[None for _ in range(8)] for _ in range(8)]
        # for img_i in range(8):
        #     for img_j in range(8):
        #         ttests[img_i][img_j] = ttest_ind(
        #             img_datas[img_i],
        #             img_datas[img_j],
        #             equal_var=False
        #         ).pvalue
        # sheet_data += ttests

        # pd.DataFrame(sheet_data).to_excel(writer, sheet_name=f"{MERSI_BAND} {MODIS_BAND}", index=False, header=False)

    # writer.close()


def show_relation_image(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    im1 = img_mersi.radiance.copy()
    im2 = img_mersi.radiance.copy()

    mask_mersi = np.zeros_like(img_mersi.radiance, dtype=bool)
    for (mersi_i, mersi_j), (modis_i, modis_j) in pixels:
        mask_mersi[mersi_i, mersi_j] = True
        im2[mersi_i, mersi_j] /= img_modis.radiance[modis_i, modis_j]

    im2[~mask_mersi] = 0

    fig, ax = plt.subplots(ncols=2)
    ax[0].imshow(im1)
    ax[1].imshow(im2)

    ax[0].set_title("MERSI-2 image")
    ax[1].set_title("MERSI-2 matching pixels")

    plt.show()


def pixels_relation_relplot():
    for MERSI_BAND, MODIS_BAND in pairs:
        print("RELATION", MERSI_BAND, MODIS_BAND)
        file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
        df = pd.read_pickle(file_path)

        fig, axes = plt.subplots(ncols=4, nrows=2, sharex=True, sharey=True)
        fig.set_figheight(15)
        fig.set_figwidth(30)
        for img_i in range(8):
            i = img_i // 4
            j = img_i % 4
            ax = axes[i][j]
            data = df[df["image_number"] == img_i]
            data = data.sample(n=min(10000, len(data)))
            relplot_with_linregress(
                data["mersi_rad"],
                data["modis_rad"],
                ax,
            )

        # plt.savefig(f"stability test/graphs/{MERSI_BAND} {MODIS_BAND}.png")
        # plt.close()
        plt.show()


def calibration(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    plt.plot(img_mersi.blackbody)
    plt.plot(img_mersi.space_view)
    plt.plot(img_mersi.voc)
    plt.legend(["Blackbody", "Space View", "VOC"])
    plt.show()


def multiple_calibration(mersi_band):
    bb = []
    sv = []
    voc = []

    for i, img_mersi in enumerate(iterate_mersi(
            band=mersi_band,
            interval=(
                    datetime(2024, 9, 4, 14, 20),
                    datetime(2024, 9, 4, 14, 40),
            )
    )):
        bb.append(img_mersi.blackbody)
        sv.append(img_mersi.space_view)
        voc.append(img_mersi.voc)
        print(i)

    plt.plot(np.concatenate(bb))
    plt.plot(np.concatenate(sv))
    plt.plot(np.concatenate(voc))
    plt.legend(["Blackbody", "Space View", "VOC"])
    # plt.show()


def show_pixel_outliers(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    stats = matching.matching_stats(img_mersi, img_modis, pixels)
    colored_img = img_mersi.colored_image()
    output = np.zeros_like(colored_img)
    center = 1.9
    eps = 0.3
    for (mersi_pixel, modis_pixel), (_, stats_row) in zip(pixels, stats.iterrows()):
        if abs(stats_row["rad_relation"] - center) > eps:
            output[*mersi_pixel] = [255, 0, 0]
        else:
            output[*mersi_pixel] = colored_img[*mersi_pixel]

    _, ax = plt.subplots(ncols=3)
    ax[0].imshow(colored_img)
    ax[1].imshow(output)
    ax[0].sharex(ax[1])
    ax[0].sharey(ax[1])
    stats = stats.sample(min(len(stats), 10000))
    relplot_with_linregress(stats["mersi_rad"], stats["modis_rad"], ax[2])
    plt.show()



# recalculate_matching_pixels()
# save_stats()
# look_at_matching_pixels()

pixels_relation_relplot()
# process_stats()
# iterate_images(georeference_stability)
# iterate_images(show_relation_image)
# iterate_images(calibration, mersi_band="10")

# multiple_calibration("18")
# plt.show()
# plt.savefig("18 calib.png")
# plt.close()
# multiple_calibration("10")
# plt.show()
# plt.savefig("10 calib.png")

# iterate_images(show_pixel_outliers)
