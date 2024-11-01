from datetime import datetime

import cv2
import matplotlib.pyplot as plt
import numpy as np

from processing.load_imagery import iterate_modis


def look_at_clouds():
    for img in iterate_modis(
            "8",
            (
                    datetime(2024, 9, 4, 14, 20),
                    datetime(2024, 9, 4, 14, 50),
            )
    ):
        _, ax = plt.subplots(nrows=2, ncols=3, sharex=True, sharey=True)

        cm = img.cloud_mask
        ax[0, 0].imshow(cm == 0)
        ax[0, 0].set_title("cloudy")
        ax[0, 1].imshow(cm == 1)
        ax[0, 1].set_title("uncertain clear")
        ax[0, 2].imshow(cm == 2)
        ax[0, 2].set_title("probably clear")
        ax[1, 0].imshow(cm == 3)
        ax[1, 0].set_title("confident clear")
        ax[1, 1].imshow(img.colored_image())
        plt.show()


def cloud_movement_correction():
    for img in iterate_modis(
            "8",
            (
                    datetime(2024, 9, 4, 14, 20),
                    datetime(2024, 9, 4, 14, 50),
            )
    ):
        _, ax = plt.subplots(nrows=2, ncols=3, sharex=True, sharey=True)
        cloud_mask = img.cloud_mask != 3
        cloud_mask = cloud_mask.astype(np.uint8) * 255
        cloud_mask_dilated = cv2.dilate(cloud_mask, np.ones((5, 5), dtype=np.uint8))
        cloud_mask_eroded = cv2.erode(cloud_mask, np.ones((5, 5), dtype=np.uint8))
        trace = cloud_mask_dilated ^ cloud_mask_eroded

        ax[0, 0].imshow(img.colored_image())
        ax[0, 1].imshow(cloud_mask)
        ax[1, 0].imshow(cloud_mask_dilated)
        ax[1, 0].set_title("dilated")
        ax[1, 1].imshow(cloud_mask_eroded)
        ax[1, 1].set_title("eroded")
        ax[1, 2].imshow(trace)
        ax[1, 2].set_title("trace")
        plt.show()


cloud_movement_correction()