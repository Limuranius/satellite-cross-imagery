import pathlib

import pandas as pd
import matplotlib.pyplot as plt

from visuals.graphs import relplot_with_linregress, boxplot_with_stats, save_fig_to_path

GRAPHS_PATH = pathlib.Path() / "Графики"

CONVERT_MERSI_BAND = {
    # (MERSI_WV, MODIS_WV, AERONET_WV)
    "8": (412, 412, 412),  # MERSI: 412
    "9": (443, 443, 443),  # MERSI: 443
    "10": (490, 488, 490),  # MERSI: 490
    # "11": (555, 555, 555),  # MERSI: 555
    "12": (670, 667, 667),  # MERSI: 670
    # "13": (709, None, 709),  # MERSI: 709
    # "14": (746, 748, None),  # MERSI: 746
    "15": (865, 869, 865),  # MERSI: 865
}


def cross(
        mersi_column: str,
        modis_column: str,
        aeronet_column: str,
):
    """
    Строит 3 графика:
        MERSI - MODIS
        MERSI - AERONET
        MODIS - AERONET

    Нужно указать название колонок из таблицы
    """
    no_nans = df[~(df[aeronet_column].isna() | df[modis_column].isna())]
    mersi = no_nans[mersi_column]
    modis = no_nans[modis_column]
    aeronet = no_nans[aeronet_column]
    _, axis = plt.subplots(ncols=3, figsize=(12, 6))
    relplot_with_linregress(mersi, modis, axis[0], s=3)
    relplot_with_linregress(mersi, aeronet, axis[1], s=3)
    relplot_with_linregress(modis, aeronet, axis[2], s=3)
    axis[0].set_title("MERSI - MODIS")
    axis[1].set_title("MERSI - AERONET")
    axis[2].set_title("MODIS - AERONET")

    axis[0].set_xlabel(f"MERSI {mersi_column}")
    axis[1].set_xlabel(f"MERSI {mersi_column}")
    axis[2].set_xlabel(f"MODIS {modis_column}")

    axis[0].set_ylabel(f"MODIS {modis_column}")
    axis[1].set_ylabel(f"AERONET {aeronet_column}")
    axis[2].set_ylabel(f"AERONET {aeronet_column}")

    plt.tight_layout()


def parallel(column_names: list[str]):
    """
    Строит на одном графике измерения нескольких столбцов
    По оси X - номер снимка
    """
    y = [df[col] for col in column_names]
    for row in y:
        plt.plot(row)
    plt.xlabel("Номер снимка")
    plt.legend(column_names)


def calibration_vs_original_difference():
    """
    Показывает разницу в измерениях откалиброванных и изначальных
    """
    mersi_wavelengths = [mersi_wl for mersi_wl, _, _ in CONVERT_MERSI_BAND.values()]
    for mersi_wl, mersi_band in zip(mersi_wavelengths, CONVERT_MERSI_BAND.keys()):
        orig = df[f"mersi_original_counts_mean[{mersi_wl}nm]"]
        calib = df[f"mersi_calibrated_counts_mean[{mersi_wl}nm]"]

        # plt.plot(orig)
        # plt.plot(calib)
        # plt.show()
        #
        # plt.plot(df[f"mersi_original_counts_std[{mersi_wl}nm]"])
        # plt.plot(df[f"mersi_calibrated_counts_std[{mersi_wl}nm]"])
        # plt.show()

        diff = calib - orig
        ax = plt.subplot()
        plt.grid()
        boxplot_with_stats(diff, ax)
        ax.set_title(f"{mersi_wl}nm (band{mersi_band})")
        ax.set_xlabel("Разница")
        save_fig_to_path(GRAPHS_PATH / "Изменение калибровок" / f"{mersi_wl}nm.png")


if __name__ == '__main__':
    # BAND = "8"
    # MERSI_WV, MODIS_WV, AERONET_WV = CONVERT_MERSI_BAND[BAND]

    df = pd.read_csv("data_with_mersi_calibrated.csv", sep="\t")

    # Убираем значения с высоким STD
    df = df[df["mersi_calibrated_counts_std[412nm]"] < 100]

    # Убираем значения с нулевыми показаниям, почему-то они есть
    df = df[df["mersi_calibrated_counts_mean[412nm]"] > 100]

    # Домножаем все Rrs от MODIS на 100
    for col in df:
        if "Rrs" in col:
            df[col] *= 100

    for mersi_band, (mersi_wl, modis_wl, aeronet_wl) in CONVERT_MERSI_BAND.items():
        band_file_name = f"{mersi_wl}nm (band {mersi_band}).png"

        # Излучение, MERSI без атм. коррекции
        cross(
            mersi_column=f"mersi_calibrated_radiance_norm_mean[{mersi_wl}nm]",
            modis_column=f"nir_Lt_{modis_wl}_mean",
            aeronet_column=f"aeronet_Lwn_f/Q[{aeronet_wl}nm]",
        )
        save_fig_to_path(GRAPHS_PATH / "Кросс (излучение без атм. коррекции)" / band_file_name)

        # Излучение, MERSI с атм. коррекцией
        cross(
            mersi_column=f"mersi_calibrated_6S_radiance_mean[{mersi_wl}nm]",
            modis_column=f"nir_Lt_{modis_wl}_mean",
            aeronet_column=f"aeronet_Lwn_f/Q[{aeronet_wl}nm]",
        )
        save_fig_to_path(GRAPHS_PATH / "Кросс (излучение с атм. коррекцией)" / band_file_name)

        # Rrs, MERSI с атм. коррекцией
        cross(
            mersi_column=f"mersi_calibrated_6S_reflectance_mean[{mersi_wl}nm]",
            modis_column=f"nir_Rrs_{modis_wl}_mean",
            aeronet_column=f"aeronet_Lwn_f/Q[{aeronet_wl}nm]",
        )
        save_fig_to_path(GRAPHS_PATH / "Кросс (Rrs с атм. коррекцией)" / band_file_name)

        # Rrs, MERSI без атм. коррекцией
        cross(
            mersi_column=f"mersi_calibrated_apparent_reflectance_mean[{mersi_wl}nm]",
            modis_column=f"nir_Rrs_{modis_wl}_mean",
            aeronet_column=f"aeronet_Lwn_f/Q[{aeronet_wl}nm]",
        )
        save_fig_to_path(GRAPHS_PATH / "Кросс (Rrs без атм. коррекции)" / band_file_name)

        # Сравнение калиброванного MERSI и некалиброванного
        # (Разница)
        calibration_vs_original_difference()

        # Параллельно излучения
        parallel(column_names=[
            f"mersi_calibrated_radiance_mean[{mersi_wl}nm]",
            f"mersi_calibrated_radiance_norm_mean[{mersi_wl}nm]",
            f"mersi_calibrated_6S_radiance_mean[{mersi_wl}nm]",
            f"nir_Lt_{modis_wl}_mean",
        ])
        save_fig_to_path(GRAPHS_PATH / "Данные параллельно (излучение)" / band_file_name)

        # Параллельно Rrs
        parallel(column_names=[
            f"mersi_calibrated_reflectance_mean[{mersi_wl}nm]",
            f"mersi_calibrated_apparent_reflectance_mean[{mersi_wl}nm]",
            f"mersi_calibrated_6S_reflectance_mean[{mersi_wl}nm]",
            f"nir_Rrs_{modis_wl}_mean",
        ])
        save_fig_to_path(GRAPHS_PATH / "Данные параллельно (Rrs)" / band_file_name)
