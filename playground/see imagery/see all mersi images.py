from matplotlib import pyplot as plt

from processing import MERSIImage
MERSIImage.LAZY_MODE = True

for dt in MERSIImage.MERSIImage.all_dts()[::-1]:
    img = MERSIImage.MERSIImage.from_dt(dt, "12")
    plt.imshow(img.counts)
    plt.title(str(dt))
    plt.show()