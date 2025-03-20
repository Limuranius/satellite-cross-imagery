from processing.MERSIImage import MERSIImage
from . import (
    manually_draw_edges,
    fix_channel_8,
    fix_channel_12,
    fix_zebra,
)


def full_correct_image(
        image: MERSIImage,
        remove_zebra: bool,
        remove_neighbor_influence: bool,
        remove_trace: bool,
) -> None:
    if remove_zebra:
        fix_zebra.apply_coeffs.correct_mersi_image(image)
    match image.band:
        case "8":
            if remove_neighbor_influence:
                fix_channel_8.apply_coeffs.correct_mersi_image(image)
        case "12":
            if remove_trace:
                fix_channel_12.apply_coeffs.correct_mersi_image(image)