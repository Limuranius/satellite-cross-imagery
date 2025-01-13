from datetime import datetime

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage
import calibration
from processing.MatchingImageryPair import MatchingImageryPair
from processing.load_imagery import iterate_image_groups
from processing.preprocessing import manual_group
from visuals.graphs import relplot_with_linregress


matplotlib.rcParams['figure.figsize'] = (16, 8)


def full_correct_image(
        image: MERSIImage,
        remove_zebra: bool,
        remove_neighbor_influence: bool,
        remove_trace: bool,
) -> None:
    if remove_zebra:
        calibration.fix_zebra.apply_coeffs.correct_mersi_image(image)
    match image.band:
        case "8":
            if remove_neighbor_influence:
                calibration.fix_channel_8.apply_coeffs.correct_mersi_image(image)
        case "12":
            if remove_trace:
                calibration.fix_channel_12.apply_coeffs.correct_mersi_image(image)


def see_results(
        image: MERSIImage,
        remove_zebra: bool,
        remove_neighbor_influence: bool,
        remove_trace: bool,
):
    before = image.counts.copy()
    full_correct_image(image, remove_zebra, remove_neighbor_influence, remove_trace)
    after = image.counts.copy()

    fig, ax = plt.subplots(ncols=3, sharey=True, sharex=True)
    ax[0].imshow(before)
    ax[1].imshow(after)
    ax[2].imshow(after - before)
    ax[0].set_title("До коррекции полосатости")
    ax[1].set_title("После коррекции полосатости")
    ax[2].set_title("Разница")
    plt.tight_layout()

    # Make a horizontal slider to control the frequency.
    min_slider = Slider(
        ax=fig.add_axes([0.1, 0.95, 0.65, 0.03]),
        label='Min',
        valmin=0,
        valmax=4096,
        valinit=0,
    )
    max_slider = Slider(
        ax=fig.add_axes([0.1, 0.9, 0.65, 0.03]),
        label='Max',
        valmin=0,
        valmax=4096,
        valinit=4096,
    )

    def update(*args):
        vmin = min_slider.val
        vmax = max_slider.val
        ax[0].clear()
        ax[1].clear()
        ax[0].imshow(before, vmin=vmin, vmax=vmax)
        ax[1].imshow(after, vmin=vmin, vmax=vmax)
        fig.canvas.draw_idle()

    min_slider.on_changed(update)
    max_slider.on_changed(update)
    plt.show()


def check_band8(matching_pair: MatchingImageryPair):
    transform_coeff = 1 / 0.479

    stats_before = matching_pair.matching_stats()
    full_correct_image(matching_pair.img_mersi, remove_zebra=True, remove_neighbor_influence=False, remove_trace=False)
    stats_after = matching_pair.matching_stats()

    stats_before = stats_before[stats_before["mersi_y"] % 10 == 0]
    stats_after = stats_after[stats_after["mersi_y"] % 10 == 0]

    assert len(stats_before) == len(stats_after)

    sensor_0_df = pd.DataFrame({
        "mersi_rad_orig": stats_before["mersi_rad"],
        "mersi_rad_calib": stats_after["mersi_rad"],
        "modis_rad_orig": stats_before["modis_rad"],
        "modis_rad_transformed": (stats_before["modis_rad"] * transform_coeff),
        "mersi_counts_orig": stats_before["mersi_counts"],
        "mersi_counts_calib": stats_after["mersi_counts"],
    })

    diff_before = sensor_0_df["mersi_rad_orig"] - sensor_0_df["modis_rad_transformed"]
    diff_after = sensor_0_df["mersi_rad_calib"] - sensor_0_df["modis_rad_transformed"]
    _, ax = plt.subplots(ncols=2, sharex=True, sharey=True)
    ax[0].hist(diff_before, bins=50)
    ax[0].set_title("Before")
    ax[1].hist(diff_after, bins=50)
    ax[1].set_title("After")
    mean_diff = diff_after.mean() - diff_before.mean()
    std_diff = diff_after.std() - diff_before.std()
    print(f"Delta mean: {mean_diff:.04f}, {(mean_diff / diff_before.mean()) * 100:.03f}%")
    print(f"Delta std: {std_diff:.04f}, {(std_diff / diff_before.std()) * 100:.03f}%")
    plt.show()

    rel_before = sensor_0_df["mersi_rad_orig"] / sensor_0_df["modis_rad_transformed"]
    rel_after = sensor_0_df["mersi_rad_calib"] / sensor_0_df["modis_rad_transformed"]
    _, ax = plt.subplots(ncols=2, sharex=True, sharey=True)
    ax[0].hist(rel_before, bins=50)
    ax[0].set_title("Before")
    ax[1].hist(rel_after, bins=50)
    ax[1].set_title("After")
    mean_diff = rel_after.mean() - rel_before.mean()
    std_diff = rel_after.std() - rel_before.std()
    print(f"Delta mean: {mean_diff:.04f}, {(mean_diff / rel_before.mean()) * 100:.03f}%")
    print(f"Delta std: {std_diff:.04f}, {(std_diff / rel_before.std()) * 100:.03f}%")
    plt.show()

    # _, ax = plt.subplots(ncols=2, sharex=True, sharey=True)
    # ax[0].hist(sensor_0_df["mersi_counts_orig"], bins=50)
    # ax[0].set_title("Before")
    # ax[1].hist(sensor_0_df["mersi_counts_calib"], bins=50)
    # ax[1].set_title("After")
    # plt.show()

    # plt.plot(sensor_0_df["mersi_counts_orig"] - sensor_0_df["mersi_counts_calib"])
    # plt.show()

    # plt.plot(sensor_0_df["mersi_rad_orig"].tolist())
    # plt.plot(sensor_0_df["mersi_rad_calib"].tolist())
    # plt.plot(sensor_0_df["modis_rad_transformed"].tolist())
    # plt.legend(["MERSI orig", "MERSI calib", "MODIS transformed"])
    # plt.title("Данные до и после калибровки датчика 0 канала 8")
    # plt.xlabel("pixel index")
    # plt.ylabel("radiance")
    # plt.show()

    # plt.plot((sensor_0_df["mersi_rad_orig"] - sensor_0_df["modis_rad_transformed"]).tolist())
    # plt.plot((sensor_0_df["mersi_rad_calib"] - sensor_0_df["modis_rad_transformed"]).tolist())
    # plt.legend(["До коррекци", "После коррекции"])
    # plt.xlabel("pixel index")
    # plt.ylabel("MERSI radiance - MODIS radiance")
    # plt.show()


def before_after_stats(
        matching_pair: MatchingImageryPair,
        remove_zebra: bool,
        remove_neighbor_influence: bool,
        remove_trace: bool,
        sensors: list[int] = None,
):
    """
    Поля:
        modis_rad
        modis_counts
        mersi_rad_orig
        mersi_rad_calib
        mersi_counts_orig
        mersi_counts_calib
    """
    img_before = matching_pair.img_mersi.counts.copy()
    full_correct_image(
        matching_pair.img_mersi,
        remove_zebra=True,
        remove_neighbor_influence=False,
        remove_trace=False,
    )

    stats_before = matching_pair.matching_stats()
    full_correct_image(
        matching_pair.img_mersi,
        remove_zebra=False,
        remove_neighbor_influence=True,
        remove_trace=True,
    )
    stats_after = matching_pair.matching_stats()
    matching_pair.img_mersi.counts = img_before

    if sensors:
        stats_before = stats_before[(stats_before["mersi_y"] % 10).isin(sensors)]
        stats_after = stats_after[(stats_after["mersi_y"] % 10).isin(sensors)]

    return pd.DataFrame({
        "modis_rad": stats_before["modis_rad"],
        "modis_counts": stats_before["modis_counts"],
        "mersi_rad_orig": stats_before["mersi_rad"],
        "mersi_rad_calib": stats_after["mersi_rad"],
        "mersi_counts_orig": stats_before["mersi_counts"],
        "mersi_counts_calib": stats_after["mersi_counts"],
    })


def see_graphs_change(
        matching_pair: MatchingImageryPair,
        remove_zebra: bool,
        remove_neighbor_influence: bool,
        remove_trace: bool,
        sensors=None,
):
    stats = before_after_stats(matching_pair, remove_zebra, remove_neighbor_influence, remove_trace, sensors=sensors)
    stats_sample = stats.sample(15000)

    # fig, ax = plt.subplots(nrows=2, ncols=3)

    _, axis = plt.subplot_mosaic("ABC;DEC")

    mersi_dn_before = stats_sample["mersi_counts_orig"]
    mersi_dn_after = stats_sample["mersi_counts_calib"]
    modis_dn = stats_sample["modis_counts"]
    mersi_rad_before = stats_sample["mersi_rad_orig"]
    mersi_rad_after = stats_sample["mersi_rad_calib"]
    modis_rad = stats_sample["modis_rad"]

    # Зависимость MERSI_RAD - MODIS_RAD
    relplot_with_linregress(mersi_rad_before, modis_rad, axis["A"])
    axis["A"].set_xlabel("MERSI radiance")
    axis["A"].set_ylabel("MODIS radiance")
    axis["A"].set_title("Before")
    relplot_with_linregress(mersi_rad_after, modis_rad, axis["D"])
    axis["D"].set_xlabel("MERSI radiance")
    axis["D"].set_ylabel("MODIS radiance")
    axis["D"].set_title("After")

    # Зависимость MERSI_RAD - MODIS_RAD / MERSI_RA
    relplot_with_linregress(mersi_rad_before, modis_rad / mersi_rad_before, axis["B"])
    axis["B"].set_xlabel("MERSI radiance")
    axis["B"].set_ylabel("MODIS radiance / MERSI radiance")
    axis["B"].set_title("Before")
    relplot_with_linregress(mersi_rad_after, modis_rad / mersi_rad_after, axis["E"])
    axis["E"].set_xlabel("MERSI radiance")
    axis["E"].set_ylabel("MODIS radiance / MERSI radiance")
    axis["E"].set_title("After")

    # Гистограмма MODIS_RAD / MERSI_RAD
    rel_before = stats["modis_rad"] / stats["mersi_rad_orig"]
    rel_after = stats["modis_rad"] / stats["mersi_rad_calib"]
    axis["C"].hist(rel_before, bins=50, alpha=0.5)
    axis["C"].hist(rel_after, bins=50, alpha=0.5)
    axis["C"].set_xlabel("MODIS radiance / MERSI radiance")
    text = f"""std_before={rel_before.std():.05f}
std_after={rel_after.std():.05f}
relative difference = {(rel_after.std() - rel_before.std()) / rel_before.std():.02%}"""
    axis["C"].text(
        0,
        0.99,
        text,
        horizontalalignment='left',
        verticalalignment='top',
        transform=axis["C"].transAxes,
    )
    # plt.show()

    axis["A"].set_xlim(0, 60)
    axis["B"].set_xlim(0, 60)
    axis["D"].set_xlim(0, 60)
    axis["E"].set_xlim(0, 60)

    axis["A"].set_ylim(0, 50)
    axis["B"].set_ylim(0.6, 0.9)
    axis["D"].set_ylim(0, 50)
    axis["E"].set_ylim(0.6, 0.9)

    axis["C"].set_xlim(0.6, 0.9)



def check_band12(matching_pair: MatchingImageryPair):
    img_before = matching_pair.img_mersi.counts.copy()
    calibration.fix_channel_12.apply_coeffs.correct_mersi_image(matching_pair.img_mersi)
    img_after = matching_pair.img_mersi.counts.copy()
    _, ax = plt.subplots(ncols=2, sharey=True, sharex=True)
    ax[0].imshow(img_before, vmin=350, vmax=700)
    ax[1].imshow(img_after, vmin=350, vmax=700)
    ax[0].set_title("До калибровки")
    ax[1].set_title("После калибровки")
    plt.tight_layout()
    plt.show()


def check_sensors_diff(
        matching_pair: MatchingImageryPair,
        sensors: list[int],
):
    """
mersi_rad
modis_rad
rad_diff
mersi_senz
modis_senz
mersi_counts
modis_counts
mersi_solz
modis_solz
rad_relation
mersi_y

    """
    fig, ax = plt.subplots(ncols=len(sensors), sharey=True, sharex=True)
    stats = matching_pair.matching_stats()
    for i, sensor in enumerate(sensors):
        sensor_stats = stats[stats["mersi_y"] % 10 == sensor]
        sample = sensor_stats.sample(min(len(sensor_stats), 15000))
        relplot_with_linregress(sample["mersi_rad"], sample["modis_rad"] / sample["mersi_rad"], ax[i])
        ax[i].set_title(f"Датчик {sensor}")
    plt.show()

OVERLAPPING_IMAGERY_DTS = [
    datetime(2024, 2, 11, 23, 00),
    # datetime(2024, 2, 11, 23, 5),
    # datetime.fromisoformat("2024-02-04 08:20:00"),
    # datetime.fromisoformat("2024-06-06 19:35:00"),
]

if __name__ == '__main__':
    mersi_band, modis_band = {
        8: ("8", "8"),
        9: ("9", "9"),
        10: ("10", "10"),
        12: ("12", "13lo"),
        15: ("15", "16"),
    }[12]

    for matching_pair in iterate_image_groups(
            groups=manual_group(
                mersi_dts=OVERLAPPING_IMAGERY_DTS,
                modis_dts=OVERLAPPING_IMAGERY_DTS,
            ),
            mersi_band=mersi_band,
            modis_band=modis_band,
    ):
        # see_results(
        #     matching_pair.img_mersi,
        #     remove_zebra=False,
        #     remove_neighbor_influence=True,
        #     remove_trace=True,
        # )
        # check_band8(matching_pair)
        # for sensor in range(10):
        for sensor in [0, 5, 9, 1, 2, 3, 4, 6, 7, 8]:
            see_graphs_change(
                matching_pair,
                remove_zebra=True,
                remove_neighbor_influence=False,
                remove_trace=True,
                sensors=[sensor, ]
            )
            plt.tight_layout()
            plt.savefig(f"/home/gleb123/Документы/28.11.24/12/{sensor}.png")
            plt.close()
        # check_band12(matching_pair)


        # plt.imshow(matching_pair.img_mersi.counts)
        # plt.show()
        #
        # plt.hist(matching_pair.img_mersi.counts.flatten(), bins=100)
        # plt.show()