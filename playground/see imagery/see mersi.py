import datetime

import matplotlib.pyplot as plt

from processing.MERSIImage import MERSIImage
import plotly.express as px

BAND = "8"
SEE_COLOR = True

img = MERSIImage.from_dt(
    datetime.datetime(2020, 5, 16, 20, 55),
    BAND
)

if SEE_COLOR:
    plt.imshow(img.colored_image())
    plt.show()
else:
    plt.imshow(img.counts)
    plt.show()