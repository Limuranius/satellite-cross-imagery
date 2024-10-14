import datetime

import matplotlib.pyplot as plt

from light_info.utils import find_similar_images

pairs = find_similar_images(
    start=datetime.date(2024, 1, 1),
    end=datetime.date(2024, 4, 1),
    lon=-43,
    lat=69,
    min_intersection_percent=0.3,
    max_time_delta=datetime.timedelta(minutes=10)
)

for info_mersi, _ in pairs:
    plt.imshow(info_mersi.get_preview())
    plt.show()
