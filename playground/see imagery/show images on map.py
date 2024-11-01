import folium

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from utils import reverse_coords, fix_antimeridian

img_mersi = MERSIImage(
    "/imagery/MERSI-2/L1/FY3D_MERSI_GBAL_L1_20240912_0350_1000M_MS.HDF",
    "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1 GEO/FY3D_MERSI_GBAL_L1_20240912_0350_GEO1K_MS.HDF",
    "8",
)

img_modis = MODISImage(
    "/imagery/MODIS/L1B/MYD021KM.A2024256.0345.061.2024256152131.hdf",
    "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B GEO/MYD03.A2024256.0345.061.2024256151418.hdf",
    "8",
)


map_obj = folium.Map()

folium.Polygon(
    reverse_coords(fix_antimeridian(img_mersi.get_corners_coords())),
    popup="MERSI-2",
).add_to(map_obj)
folium.Polygon(
    reverse_coords(fix_antimeridian(img_modis.get_corners_coords())),
    popup="MODIS",
).add_to(map_obj)

map_obj.show_in_browser()