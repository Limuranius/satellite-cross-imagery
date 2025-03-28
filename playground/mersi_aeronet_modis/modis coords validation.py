import datetime

from processing.MODISImage import MODISImage

img = MODISImage.from_dt(
    datetime.datetime.fromisoformat("2020-11-22 13:10:00"),
    "8",
)
print(img)
