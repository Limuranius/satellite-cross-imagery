import math
from datetime import datetime, timedelta

import h5py
import matplotlib
import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt
import seaborn as sns
from pyhdf.SD import SD
from scipy.stats import linregress

from processing import matching
from processing.MERSIImage import MERSIImage, MERSI_2_BANDS
from processing.MODISImage import MODISImage, MODIS_BANDS
from processing.load_imagery import iterate_close_images, iterate_mersi, iterate_modis, iterate_image_groups
from processing.matching import visualize_matching_pixels, load_matching_pixels
from processing.preprocessing import manual_group
from utils import datetime_range

from visuals.graphs import relplot_with_linregress
import visuals.map_2d

matplotlib.rcParams['figure.figsize'] = (20, 10)

MATCHING_PIXELS_KWARGS = dict(
    max_zenith_relative_diff=0.05,
    max_zenith=3000,
    exclude_clouds=False,
    exclude_land=False,
    exclude_water=False,
    do_erosion=False,
    correct_cloud_movement=False,
    use_rstd_filtering=True,
    rstd_kernel_size=5,
    rstd_threshold=0.05,
)

pairs = [
    ("8", "8"),
    # ("9", "9"),
    # ("10", "10"),
    # ("11", "12"),
    # ("12", "13lo"),
    # ("12", "14lo"),
]

OVERLAPPING_SWATH_START = datetime(2024, 9, 4, 14, 20)
OVERLAPPING_SWATH_END = datetime(2024, 9, 4, 14, 55)

generate_iterator = lambda mersi_band, modis_band: iterate_image_groups(
    groups=manual_group(
        mersi_dts=list(datetime_range(
            OVERLAPPING_SWATH_START,
            OVERLAPPING_SWATH_END,
        )),
        modis_dts=list(datetime_range(
            OVERLAPPING_SWATH_START,
            OVERLAPPING_SWATH_END,
        )),
    ),
    mersi_band=mersi_band,
    modis_band=modis_band,
)


def iterate_images(func, mersi_band="8", modis_band="8", force_recalculate=False):
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(mersi_band, modis_band)):
        pixels = load_matching_pixels(
            img_mersi, img_modis,
            **MATCHING_PIXELS_KWARGS,
        )
        func(img_mersi, img_modis, pixels)
        print(i)


def look_at_matching_pixels():
    MERSI_BAND = "8"
    MODIS_BAND = "8"
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
        pixels = load_matching_pixels(
            img_mersi, img_modis, **MATCHING_PIXELS_KWARGS,
        )
        visualize_matching_pixels(
            img_mersi,
            img_modis,
            pixels
        )
        plt.show()
        # plt.savefig(f"stability test/images/{i}.png")
        # plt.close()
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
            # force_recalculate=True
            **MATCHING_PIXELS_KWARGS,
        )

        # visualize_matching_pixels(img_mersi, img_modis, pixels)
        # plt.show()


def save_stats():
    for MERSI_BAND, MODIS_BAND in pairs:
        print(MERSI_BAND, MODIS_BAND)
        dfs = []
        for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
            pixels = load_matching_pixels(img_mersi, img_modis, **MATCHING_PIXELS_KWARGS)

            apply_amplifier_correction(i, img_mersi)

            # df = matching.matching_stats(img_mersi, img_modis, pixels)
            df = matching.aggregated_matching_stats(img_mersi, img_modis, pixels)
            df["image_number"] = i
            dfs.append(df)

            print(i)

        total_df = pd.concat(dfs)
        file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
        total_df.to_pickle(file_path)


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
            data = data.sample(n=min(15000, len(data)))
            relplot_with_linregress(
                data["mersi_rad"],
                data["modis_rad"],
                ax,
            )
            ax.set_xlabel("MERSI-2 radiance")
            ax.set_ylabel("MODIS radiance")
            ax.set_title(str(img_i))

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
                    OVERLAPPING_SWATH_START - timedelta(minutes=20),
                    OVERLAPPING_SWATH_END,
            )
    )):
        bb.append(img_mersi.blackbody)
        sv.append(img_mersi.space_view)
        voc.append(img_mersi.voc)
        print(i)

    bb = np.concatenate(bb)
    sv = np.concatenate(sv)
    voc = np.concatenate(voc)

    bb[1199] = bb[1198]
    sv[1199] = sv[1198]
    voc[1199] = voc[1198]

    # Убираем изменчивость усилителя
    level0 = bb[0]
    # bb_amplifier = bb / level0
    # voc_amplifier = voc / level0
    diff = voc[1500] - bb[1500]
    amplifier = bb / level0

    fig, ax = plt.subplots(ncols=2)
    ax[0].plot(bb)
    ax[0].plot(sv)
    ax[0].plot(voc)
    ax[0].vlines(range(0, len(bb), 200), ymin=min(bb), ymax=max(sv))
    ax[0].legend(["Blackbody", "Space View", "VOC"])
    ax[0].set_title(f"MERSI-2, Band {mersi_band}, start={OVERLAPPING_SWATH_START}, end={OVERLAPPING_SWATH_END}")
    ax[0].set_ylabel("DN")

    # l = linregress(voc[800:], bb[800:])
    # ax[1].plot(bb)
    # ax[1].plot(voc * l.slope + l.intercept)

    # ax[1].plot(amplifier)

    # np.save("amplifier", amplifier[800:])

    # relplot_with_linregress(voc[800:], bb[800:], ax[1])


def show_pixel_outliers(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    stats = matching.matching_stats(img_mersi, img_modis, pixels)
    colored_img = img_mersi.colored_image()
    output = np.zeros_like(colored_img)
    center = 0.49
    eps = 0.4
    for (mersi_pixel, modis_pixel), (_, stats_row) in zip(pixels, stats.iterrows()):
        output[*mersi_pixel] = colored_img[*mersi_pixel]
        # if abs(1 / stats_row["rad_relation"] - center) > eps:
        #     output[*mersi_pixel] = [255, 0, 0]
        # else:
        #     output[*mersi_pixel] = colored_img[*mersi_pixel]

    _, ax = plt.subplots(ncols=3)
    ax[0].imshow(colored_img)
    ax[1].imshow(output)
    ax[0].sharex(ax[1])
    ax[0].sharey(ax[1])
    stats = stats.sample(min(len(stats), 10000))
    relplot_with_linregress(stats["mersi_rad"], stats["modis_rad"], ax[2])
    plt.show()


def apply_amplifier_correction(
        img_i: int,
        img_mersi: MERSIImage,
):
    amplifier_coeffs = np.load("amplifier.npy")
    for i in range(200):
        img_mersi.radiance[10 * i: 10 * (i + 1)] *= amplifier_coeffs[img_i * 200 + i]


def are_coefficients_same():
    mersi_band = "8"
    modis_band = "8"
    df = pd.DataFrame(columns=["MERSI Coeff0", "MERSI Coeff1", "MERSI Coeff2", "MODIS Slope", "MODIS Intercept"])
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(mersi_band, modis_band)):
        Cal_0, Cal_1, Cal_2 = h5py.File(img_mersi.file_path)["Calibration"]["VIS_Cal_Coeff"][MERSI_2_BANDS.index(mersi_band)]
        RefSB = SD(img_modis.file_path).select("EV_1KM_RefSB")
        radiance_scale = RefSB.attributes()["radiance_scales"][MODIS_BANDS.index(modis_band)]
        radiance_offset = RefSB.attributes()["radiance_offsets"][MODIS_BANDS.index(modis_band)]
        df.loc[len(df)] = [Cal_0, Cal_1, Cal_2, radiance_scale, radiance_offset]
    print(df)


def bbsvvoc_radiance_correlation():
    bb = []
    sv = []
    voc = []

    for i, img_mersi in enumerate(iterate_mersi(
            band="8",
            interval=(
                    OVERLAPPING_SWATH_START - timedelta(minutes=0),
                    OVERLAPPING_SWATH_END,
            )
    )):
        bb.append(img_mersi.blackbody)
        sv.append(img_mersi.space_view)
        voc.append(img_mersi.voc)
        print(i)

    bb = np.concatenate(bb)
    sv = np.concatenate(sv)
    voc = np.concatenate(voc)

    bb[399] = bb[398]
    sv[399] = sv[398]
    voc[399] = voc[398]

    fig, ax = plt.subplots(ncols=2)
    ax[0].plot(bb)
    ax[0].plot(sv)
    ax[0].plot(voc)
    ax[0].vlines(range(0, len(bb), 200), ymin=min(bb), ymax=max(sv))
    ax[0].legend(["Blackbody", "Space View", "VOC"])
    ax[0].set_title(f"MERSI-2, Band 8, start={OVERLAPPING_SWATH_START}, end={OVERLAPPING_SWATH_END}")
    ax[0].set_ylabel("DN")


    file_path = f"stability test/8 8.pkl"
    df = pd.read_pickle(file_path)

    slopes = []
    for img_i in range(8):
        data = df[df["image_number"] == img_i]
        l = linregress(data["mersi_rad"], data["modis_rad"])
        print(l.slope, l.intercept, l.rvalue ** 2)
        if l.rvalue ** 2 < 0.95:
            slopes.append(None)
        else:
            slopes.append(l.slope)

    ax[1].plot(slopes)
    ax[1].set_ylabel("Slope")
    ax[1].set_xlabel("img_i")

    amplifier = sv / sv[0]
    np.save("amplifier", amplifier)

    plt.show()




# recalculate_matching_pixels()
save_stats()
# look_at_matching_pixels()

pixels_relation_relplot()
# iterate_images(georeference_stability)
# iterate_images(show_relation_image)
# iterate_images(calibration, mersi_band="10")

# for mersi_band in BANDS:
#     multiple_calibration(mersi_band)
#     plt.savefig(f"calibrators/{mersi_band} calibrators.png")
#     plt.close()

# bbsvvoc_radiance_correlation()
# multiple_calibration("8")
# plt.show()

# iterate_images(show_pixel_outliers)
