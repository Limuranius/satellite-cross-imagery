import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.subplots
import tqdm

import paths
import processing.matching
import utils
from custom_types import MatchingPixelsArray
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage


class MatchingImageryPair:
    img_mersi: MERSIImage
    img_modis: MODISImage

    def __init__(self, mersi: MERSIImage, modis: MODISImage):
        self.img_mersi = mersi
        self.img_modis = modis

    def matching_stats(
            self,
            pixels: list[tuple[int, int], tuple[int, int]] = None,
    ):
        if pixels is None:
            pixels = self.matching_pixels()
        return processing.matching.matching_stats(
            self.img_mersi,
            self.img_modis,
            pixels,
        )

    def aggregated_matching_stats(
            self,
            pixels: list[tuple[int, int], tuple[int, int]] = None,
            kernel_size: int = 5,
    ):
        if pixels is None:
            pixels = self.matching_pixels()
        return processing.matching.aggregated_matching_stats(
            self.img_mersi,
            self.img_modis,
            pixels,
            kernel_size,
        )

    def matching_pixels(
            self,
            mersi_mask: np.ndarray = None,
            modis_mask: np.ndarray = None,
    ) -> MatchingPixelsArray:
        filename = f"mersi={self.img_mersi.dt.isoformat()} modis={self.img_modis.dt.isoformat()}.npy"
        path = paths.MATCHING_PIXELS_DIR / filename
        if path.exists():
            matching_pixels = np.load(path)
        else:
            matching_pixels = processing.matching.get_matching_pixels(self.img_mersi, self.img_modis)
            np.save(path, matching_pixels)
        if mersi_mask is not None:
            mersi_mask = mersi_mask[matching_pixels[:, 0, 0], matching_pixels[:, 0, 1]]  # converting 2d mask to 1d mask
            matching_pixels = matching_pixels[mersi_mask]
        if modis_mask is not None:
            modis_mask = modis_mask[matching_pixels[:, 1, 0], matching_pixels[:, 1, 1]]  # converting 2d mask to 1d mask
            matching_pixels = matching_pixels[modis_mask]
        return matching_pixels

    def show(
            self,
            pixels: MatchingPixelsArray = None,
            colored=True,
            use_plotly=False,
    ):
        if pixels is None:
            pixels = self.matching_pixels()
        if colored:
            colored_img_mersi = self.img_mersi.colored_image()
            colored_img_modis = self.img_modis.colored_image()
        else:
            colored_img_mersi = np.dstack(tuple([self.img_mersi.radiance] * 3))
            colored_img_modis = np.dstack(tuple([self.img_modis.radiance] * 3))
        match_mersi = np.zeros_like(colored_img_mersi)
        match_modis = np.zeros_like(colored_img_modis)
        mersi_i, mersi_j = pixels[:, 0, 0], pixels[:, 0, 1]
        modis_i, modis_j = pixels[:, 1, 0], pixels[:, 1, 1]
        match_mersi[mersi_i, mersi_j] = colored_img_mersi[mersi_i, mersi_j]
        match_modis[modis_i, modis_j] = colored_img_modis[modis_i, modis_j]

        if use_plotly:
            fig = plotly.subplots.make_subplots(cols=2, subplot_titles=[
                "MERSI\n" + self.img_mersi.dt.isoformat(),
                "MODIS\n" + self.img_modis.dt.isoformat()
            ])
            fig.add_trace(
                go.Image(z=match_mersi),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Image(z=match_modis),
                row=1,
                col=2,
            )
            return fig
        else:
            fig, ax = plt.subplots(ncols=2, figsize=(10, 5))
            ax[0].imshow(match_mersi)
            ax[1].imshow(match_modis)
            ax[0].set_title("MERSI\n" + self.img_mersi.dt.isoformat())
            ax[1].set_title("MODIS\n" + self.img_modis.dt.isoformat())
            return fig

    def slice(self, x_min: int, x_max: int, y_min: int, y_max: int, plot=False, colored=True) -> tuple[
        np.ndarray, np.ndarray]:
        pixels = self.matching_pixels()
        y, x = pixels[:, 0, 0], pixels[:, 0, 1]
        pixels = pixels[(y_min <= y) & (y < y_max) & (x_min <= x) & (x < x_max)]

        if colored:
            img_mersi = self.img_mersi.colored_image()
            img_modis = self.img_modis.colored_image()
        else:
            img_mersi = self.img_mersi.radiance
            img_modis = self.img_modis.radiance

        slice_mersi = img_mersi[y_min: y_max, x_min: x_max]
        slice_modis = np.zeros_like(slice_mersi)
        for (mersi_pixel, modis_pixel) in pixels:
            y_local, x_local = mersi_pixel[0] - y_min, mersi_pixel[1] - x_min
            slice_modis[y_local, x_local] = img_modis[*modis_pixel]
        if plot:
            fig = plotly.subplots.make_subplots(cols=2, subplot_titles=[
                "MERSI",
                "MODIS",
            ])
            fig.add_trace(
                go.Image(z=slice_mersi),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Image(z=slice_modis),
                row=1,
                col=2,
            )
            fig.show()
        return slice_mersi, slice_modis

    def iou(self) -> float:
        return utils.iou(
            self.img_modis.get_corners_coords(),
            self.img_mersi.get_corners_coords(),
        )

    @classmethod
    def from_dt(
            cls,
            mersi_dt: datetime.datetime,
            modis_dt: datetime.datetime,
            band_mersi: str,
            band_modis: str
    ):
        return cls(MERSIImage.from_dt(mersi_dt, band_mersi), MODISImage.from_dt(modis_dt, band_modis))

    @classmethod
    def find_matching_dts(
            cls,
            min_iou: float = 0.3,
            td: datetime.timedelta = datetime.timedelta(minutes=0),
    ) -> list[tuple[datetime.datetime, datetime.datetime]]:
        mersi_dts = MERSIImage.all_dts()
        modis_dts = MODISImage.all_dts()
        time_matches = utils.match_dts_timedelta(
            mersi_dts,
            modis_dts,
            td,
        )
        res = []
        for dt1, dts2 in tqdm.tqdm(time_matches.items()):
            ious = [MatchingImageryPair(
                MERSIImage.from_dt(dt1, "8"),
                MODISImage.from_dt(dt2, "8"),
            ).iou() for dt2 in dts2]
            if max(ious) >= min_iou:
                best_dt2 = dts2[ious.index(max(ious))]
                res.append((dt1, best_dt2))
        return res
