from datetime import datetime
import calibration.utils
import matplotlib.pyplot as plt

from processing.MERSIImage import MERSIImage

DTS = [
    # datetime(2024, 1, 2, 8, 25),
    # datetime(2024, 2, 11, 23, 00),
    # datetime(2024, 2, 29, 15, 45),
    # datetime(2024, 4, 2, 11, 15),
    # datetime(2024, 5, 7, 17, 15),
    # datetime(2024, 5, 20, 6, 25),
    # datetime(2024, 6, 6, 19, 40),
    # datetime(2024, 6, 21, 20, 00),
    # datetime(2024, 7, 9, 7, 40),
    # datetime(2024, 8, 3, 6, 30),
    # datetime(2024, 8, 23, 5, 15),

    # datetime.fromisoformat("2024-01-07 12:00:00"),
    # datetime.fromisoformat("2024-01-22 17:25:00"),
    # datetime.fromisoformat("2024-02-04 08:20:00"),
    # datetime.fromisoformat("2024-02-22 02:40:00"),
    # datetime.fromisoformat("2024-03-25 22:10:00"),
    # datetime.fromisoformat("2024-04-15 02:05:00"),
    # datetime.fromisoformat("2024-05-07 18:55:00"),

    # datetime.fromisoformat("2024-01-12 13:50:00"),
    # datetime.fromisoformat("2024-01-17 15:40:00"),
    # datetime.fromisoformat("2024-01-22 17:30:00"),
    # datetime.fromisoformat("2024-01-30 06:35:00"),
    # datetime.fromisoformat("2024-02-04 08:20:00"),
    # datetime.fromisoformat("2024-02-06 21:15:00"),
    # datetime.fromisoformat("2024-02-09 10:10:00"),  # maybe 12
    # datetime.fromisoformat("2024-02-14 12:00:00"),
    # datetime.fromisoformat("2024-02-29 15:45:00"),
    # datetime.fromisoformat("2024-04-15 02:00:00"),
    # datetime.fromisoformat("2024-04-30 04:15:00"),
    # datetime.fromisoformat("2024-05-02 17:00:00"),
    # datetime.fromisoformat("2024-05-12 17:15:00"),  # maybe 12
    # datetime.fromisoformat("2024-05-15 06:10:00"),
    # datetime.fromisoformat("2024-06-06 19:35:00"),  # GOAT
    # datetime.fromisoformat("2024-10-01 20:00:00"),  # CHANNEL 12 GOAT

    datetime.fromisoformat("2020-06-19 11:45:00"),
]
for dt in DTS:

    img = MERSIImage.from_dt(dt, "13")


    plt.title(str(dt))
    water_color = calibration.utils.find_mean_water_brightness(img.counts)
    # plt.imshow(img.counts)
    # plt.imshow(img.counts, vmin=water_color * 0.9, vmax=water_color + 100)
    # plt.imshow(img.counts, vmin=800, vmax=1000)
    plt.imshow(img.counts)
    plt.show()
