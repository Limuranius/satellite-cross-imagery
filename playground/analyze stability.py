import math
from datetime import datetime

import h5py
import matplotlib
import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt
from pyhdf.SD import SD
from scipy.stats import linregress

from processing import matching
from processing.MERSIImage import MERSIImage, MERSI_2_BANDS
from processing.MODISImage import MODISImage, MODIS_BANDS
from processing.load_imagery import iterate_mersi, iterate_image_groups
from processing.matching import visualize_matching_pixels, load_matching_pixels
from processing.preprocessing import manual_group
from utils import datetime_range
from visuals.graphs import relplot_with_linregress, scatter_with_density

matplotlib.rcParams['figure.figsize'] = (30, 15)

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
    exclude_overflow=True,
)

MERSI_BAND, MODIS_BAND = "10", "10"

# OVERLAPPING_SWATH_START = datetime(2024, 9, 4, 14, 20)
# OVERLAPPING_SWATH_END = datetime(2024, 9, 4, 14, 55)

# OVERLAPPING_IMAGERY_DTS = [
#     *datetime_range(
#         datetime(2024, 9, 4, 14, 20),
#         datetime(2024, 9, 4, 14, 55),
#     ),
#     *datetime_range(
#         datetime(2024, 2, 11, 23, 0),
#         datetime(2024, 2, 11, 23, 35),
#     )
# ]

OVERLAPPING_IMAGERY_DTS = [
    # datetime(2024, 2, 11, 23, 20),
    *datetime_range(
        datetime(2024, 9, 4, 14, 20),
        datetime(2024, 9, 4, 14, 55),
    ),
    *datetime_range(
        datetime(2024, 2, 11, 23, 0),
        datetime(2024, 2, 11, 23, 35),
    ),
]

# OVERLAPPING_IMAGERY_DTS = [
#     *datetime_range(
#         datetime(2019, 1, 4, 22, 25),
#         datetime(2019, 1, 4, 23, 5),
#     ),
# ]

generate_iterator = lambda mersi_band, modis_band: iterate_image_groups(
    groups=manual_group(
        mersi_dts=OVERLAPPING_IMAGERY_DTS,
        modis_dts=OVERLAPPING_IMAGERY_DTS,
    ),
    mersi_band=mersi_band,
    modis_band=modis_band,
)


def iterate_images(func, mersi_band=MERSI_BAND, modis_band=MODIS_BAND):
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(mersi_band, modis_band)):
        pixels = load_matching_pixels(
            img_mersi, img_modis,
            **MATCHING_PIXELS_KWARGS,
        )
        func(img_mersi, img_modis, pixels)
        print(i)


def look_at_matching_pixels(mersi_band, modis_band):
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(mersi_band, modis_band)):
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
    for img_mersi, img_modis in tqdm.tqdm(generate_iterator(MERSI_BAND, MODIS_BAND),
                                          desc="Recalculating matching pixels"):
        pixels = load_matching_pixels(
            img_mersi, img_modis,
            # force_recalculate=True
            **MATCHING_PIXELS_KWARGS,
        )


def save_stats(
        remove_amplifier: bool,
        aggregate_stats: bool,
        split_by_y: bool
):
    dfs = []
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
        pixels = load_matching_pixels(img_mersi, img_modis, **MATCHING_PIXELS_KWARGS)

        if remove_amplifier:
            apply_amplifier_correction(img_mersi)

        if aggregate_stats:
            df = matching.aggregated_matching_stats(img_mersi, img_modis, pixels)
        else:
            df = matching.matching_stats(img_mersi, img_modis, pixels)

        # df = df[df["mersi_rad"] > 100]

        if split_by_y:
            y_window_size = 100
            win_count = 2000 // y_window_size
            df["image_number"] = win_count * i + df["mersi_y"] // y_window_size
        else:
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
    im3 = img_modis.radiance.copy()

    mask_modis = np.zeros_like(img_modis.radiance, dtype=bool)
    mask_mersi = np.zeros_like(img_mersi.radiance, dtype=bool)
    for mersi_coord, modis_coord in pixels:
        if img_modis.scaled_integers[*modis_coord] > 60000:
            continue
        if img_mersi.counts[*mersi_coord] > 4000:
            continue
        mask_mersi[*mersi_coord] = True
        mask_modis[*modis_coord] = True
        im2[*mersi_coord] = img_modis.radiance[modis_coord] / im2[mersi_coord]

    im2[~mask_mersi] = 0
    im3[~mask_modis] = 0

    fig, ax = plt.subplots(ncols=3)
    ax[0].imshow(im1)
    ax[2].imshow(im2)
    ax[1].imshow(im3)

    ax[0].set_title("MERSI-2 image")
    ax[2].set_title("MODIS rad / MERSI rad")
    ax[1].set_title("MODIS matching pixels")

    ax[0].sharex(ax[2])
    ax[0].sharey(ax[2])

    plt.show()


def pixels_relation_relplot(ncols: int, nrows: int):
    print("RELATION", MERSI_BAND, MODIS_BAND)
    file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
    df = pd.read_pickle(file_path)

    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, sharex=True, sharey=True)
    fig.set_figheight(15)
    fig.set_figwidth(30)
    for img_i in range(len(df["image_number"].unique())):
        i = img_i // ncols
        j = img_i % ncols
        ax = axes[i][j]
        data = df[df["image_number"] == img_i]
        data = data.sample(n=min(15000, len(data)))
        x = data["mersi_rad"].to_numpy().astype(float)
        y = data["modis_rad"].to_numpy().astype(float)
        relplot_with_linregress(
            x,
            y,
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
            # interval=(
            #         OVERLAPPING_SWATH_START - timedelta(minutes=20),
            #         OVERLAPPING_SWATH_END,
            # )
            # dts=[
            #         datetime(2024, 9, 4, 14, 0),
            #         datetime(2024, 9, 4, 14, 5),
            #         datetime(2024, 9, 4, 14, 10),
            #         datetime(2024, 9, 4, 14, 15),
            #     ] + OVERLAPPING_IMAGERY_DTS
            dts=OVERLAPPING_IMAGERY_DTS
    )):
        bb.append(img_mersi.blackbody)
        sv.append(img_mersi.space_view)
        voc.append(img_mersi.voc)
        print(i)

    bb = np.concatenate(bb)
    sv = np.concatenate(sv)
    voc = np.concatenate(voc)

    bb[bb == 0] = np.nan
    sv[sv == 0] = np.nan
    voc[voc == 0] = np.nan

    plt.plot(bb)
    plt.plot(sv)
    plt.plot(voc)
    plt.vlines(range(0, len(bb), 200), ymin=min(bb), ymax=max(sv))

    img_count = len(bb) // 200
    # numeration = list(range(-4, img_count - 4))
    numeration = list(range(img_count))
    for i in range(img_count):
        plt.text(i * 200 + 100, max(sv), str(numeration[i]))

    plt.legend(["Blackbody", "Space View", "VOC"])
    plt.title(f"MERSI-2, Band {mersi_band}")
    plt.ylabel("DN")

    plt.show()


def show_pixel_outliers(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    stats = matching.matching_stats(img_mersi, img_modis, pixels)
    colored_img_mersi = img_mersi.colored_image()
    colored_img_modis = img_modis.colored_image()
    match_mersi = np.zeros_like(colored_img_mersi)
    match_modis = np.zeros_like(colored_img_modis)
    for (mersi_pixel, modis_pixel), (_, stats_row) in zip(pixels, stats.iterrows()):
        match_mersi[*mersi_pixel] = colored_img_mersi[*mersi_pixel]
        match_modis[*modis_pixel] = colored_img_modis[*modis_pixel]

    _, ax = plt.subplots(ncols=3)
    _, axis = plt.subplot_mosaic("ABC;DEF")
    ax_mersi_full = axis["A"]
    ax_mersi_match = axis["B"]
    ax_relation = axis["C"]
    ax_modis_full = axis["D"]
    ax_modis_match = axis["E"]
    ax_rad_rel_relation = axis["F"]

    ax_mersi_full.imshow(colored_img_mersi)
    ax_mersi_match.imshow(match_mersi)
    ax_modis_full.imshow(colored_img_modis)
    ax_modis_match.imshow(match_modis)

    ax_mersi_full.sharex(ax_mersi_match)
    ax_mersi_full.sharey(ax_mersi_match)
    ax_modis_full.sharex(ax_modis_match)
    ax_modis_full.sharey(ax_modis_match)

    ax_mersi_full.set_title("MERSI")
    ax_relation.set_title(str(img_mersi.dt))
    ax_modis_full.set_title("MODIS")
    ax_modis_match.set_title("MODIS matched pixels")

    stats = stats.sample(min(len(stats), 15000))
    relplot_with_linregress(stats["mersi_rad"], stats["modis_rad"], ax_relation)
    ax_relation.set_xlabel("MERSI radiance")
    ax_relation.set_ylabel("MODIS radiance")

    relplot_with_linregress(stats["mersi_rad"], stats["modis_rad"] / stats["mersi_rad"], ax_rad_rel_relation)
    ax_rad_rel_relation.set_xlabel("MERSI radiance")
    ax_rad_rel_relation.set_ylabel("MODIS radiance / MERSI radiance")

    plt.tight_layout()
    plt.savefig(f"stability test/images/{img_mersi.dt}.png")
    plt.close()
    # plt.show()


def apply_amplifier_correction(
        img_mersi: MERSIImage,
):
    # amplifier_coeffs = np.load("amplifier.npy")
    # for i in range(200):
    #     img_mersi.radiance[10 * i: 10 * (i + 1)] *= amplifier_coeffs[img_i * 200 + i]

    sv = img_mersi.space_view
    bands_sv_defaults = {
        "8": 130
    }
    amplifier = sv / bands_sv_defaults[img_mersi.band]
    for i in range(200):
        img_mersi.radiance[10 * i: 10 * (i + 1)] *= amplifier[i]


def are_coefficients_same():
    df = pd.DataFrame(columns=["dt", "MERSI Coeff0", "MERSI Coeff1", "MERSI Coeff2", "MODIS Slope", "MODIS Intercept"])
    for i, (img_mersi, img_modis) in enumerate(generate_iterator(MERSI_BAND, MODIS_BAND)):
        Cal_0, Cal_1, Cal_2 = h5py.File(img_mersi.file_path)["Calibration"]["VIS_Cal_Coeff"][
            MERSI_2_BANDS.index(MERSI_BAND)]
        RefSB = SD(img_modis.file_path).select("EV_1KM_RefSB")
        radiance_scale = RefSB.attributes()["radiance_scales"][MODIS_BANDS.index(MODIS_BAND)]
        radiance_offset = RefSB.attributes()["radiance_offsets"][MODIS_BANDS.index(MODIS_BAND)]
        df.loc[len(df)] = [img_mersi.dt, Cal_0, Cal_1, Cal_2, radiance_scale, radiance_offset]
    df.to_excel("coeffs.xlsx")


def bbsvvoc_radiance_correlation():
    bb = []
    sv = []
    voc = []

    for i, img_mersi in enumerate(iterate_mersi(
            band=MERSI_BAND,
            dts=OVERLAPPING_IMAGERY_DTS
    )):
        bb.append(img_mersi.blackbody)
        sv.append(img_mersi.space_view)
        voc.append(img_mersi.voc)
        print(i)

    bb = np.concatenate(bb)
    sv = np.concatenate(sv)
    voc = np.concatenate(voc)

    bb[bb == 0] = np.nan
    sv[sv == 0] = np.nan
    voc[voc == 0] = np.nan

    fig, ax = plt.subplots(nrows=2)
    ax[0].plot(bb)
    ax[0].plot(sv)
    ax[0].plot(voc)
    ax[0].vlines(range(0, len(bb), 200), ymin=min(bb), ymax=max(sv))

    img_count = len(bb) // 200
    numeration = list(range(img_count))
    for i in range(img_count):
        ax[0].text(i * 200 + 100, max(sv), str(numeration[i]))

    ax[0].legend(["Blackbody", "Space View", "VOC"])
    ax[0].set_title(f"MERSI-2, Band {MERSI_BAND}")
    ax[0].set_ylabel("DN")

    file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
    df = pd.read_pickle(file_path)

    x = df["image_number"].unique()
    slopes = []
    for img_i in sorted(df["image_number"].unique()):
        data = df[df["image_number"] == img_i]
        # l = linregress(data["mersi_rad"], data["modis_rad"])
        # print(l.slope, l.intercept, l.rvalue ** 2, len(data))
        # if l.rvalue ** 2 < 0.7:
        #     slopes.append(None)
        # else:
        #     slopes.append(l.slope)

        relation = data["modis_rad"] / data["mersi_rad"]
        mean = relation.mean()
        print(mean, relation.std(), len(data))
        slopes.append(mean)

    ax[1].plot(x, slopes)
    ax[1].set_ylabel("Slope")
    ax[1].set_xlabel("img_i")

    # amplifier = sv / sv[0]
    # np.save("amplifier", amplifier)

    plt.show()


def slope_statistics():
    print("RELATION", MERSI_BAND, MODIS_BAND)
    file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
    df = pd.read_pickle(file_path)

    slopes_df = pd.DataFrame(columns=["slope", "intercept", "r^2", "n"])
    for img_i in df["image_number"].unique():
        image_data = df[df["image_number"] == img_i]
        lin = linregress(image_data["mersi_rad"], image_data["modis_rad"])
        slopes_df.loc[len(slopes_df)] = [lin.slope, lin.intercept, lin.rvalue ** 2, len(image_data)]

    print(slopes_df)
    print(slopes_df.to_csv())

    slopes_df.to_excel("slopes.xlsx")

    # slopes_df = slopes_df[slopes_df["r^2"] > 0.85]
    plt.hist(slopes_df["slope"])
    plt.xlabel("slope")
    plt.show()


def rad_solz_relation():
    print("RELATION", MERSI_BAND, MODIS_BAND)
    file_path = f"stability test/{MERSI_BAND} {MODIS_BAND}.pkl"
    df = pd.read_pickle(file_path)

    df = df.sample(15000)
    ax = plt.subplot()
    ax.set_xlabel("solz")
    ax.set_ylabel("MERSI radiance / MODIS radiance")
    relplot_with_linregress(df["mersi_solz"], df["rad_relation"], ax)
    # plt.scatter(df["mersi_solz"], df["rad_relation"], s=1)
    # plt.xlabel("solz")
    # plt.ylabel("MERSI radiance / MODIS radiance")
    plt.show()


def show_hist(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    plt.hist(img_mersi.radiance.flatten())
    plt.show()


def rad_rel_relation(
        img_mersi: MERSIImage,
        img_modis: MODISImage,
        pixels,
):
    limits = {
        "8": ((0, 500), (0.3, 0.7)),
        "10": ((0, 500), (0, 0.5))
    }

    stats = matching.matching_stats(img_mersi, img_modis, pixels)
    stats = stats.sample(min(15000, len(stats)))
    ax = plt.subplot()
    rel = stats["modis_rad"] / stats["mersi_rad"]
    relplot_with_linregress(stats["mersi_rad"], rel, ax)

    ax.set_xlabel("MERSI radiance")
    ax.set_ylabel("MODIS radiance / MERSI radiance")
    ax.set_xlim(*limits[img_mersi.band][0])
    ax.set_ylim(*limits[img_mersi.band][1])
    plt.title(str(img_mersi.dt))

    plt.savefig(
        f"/home/gleb123/satellite-cross-imagery/playground/stability test/images/mersi rad rel relation/{img_mersi.dt}.png")
    plt.close()
    # plt.show()


# recalculate_matching_pixels()
# save_stats(
#     remove_amplifier=False,
#     aggregate_stats=False,
#     split_by_y=True,
# )
# look_at_matching_pixels(MERSI_BAND, MODIS_BAND)

# pixels_relation_relplot(nrows=4, ncols=4)
# iterate_images(georeference_stability)
# iterate_images(show_relation_image)
# iterate_images(rad_rel_relation)
# iterate_images(calibration, mersi_band="8")

# for mersi_band in BANDS:
#     multiple_calibration(mersi_band)
#     plt.savefig(f"calibrators/{mersi_band} calibrators.png")
#     plt.close()

# bbsvvoc_radiance_correlation()
# multiple_calibration("8")

# rad_solz_relation()


iterate_images(show_pixel_outliers)
# iterate_images(show_hist)

# are_coefficients_same()
# slope_statistics()