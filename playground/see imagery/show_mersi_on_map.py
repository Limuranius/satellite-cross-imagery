import folium
import tqdm

from processing.MERSIImage import MERSIImage
from utils import reverse_coords, fix_antimeridian


map_obj = folium.Map()

for dt in tqdm.tqdm(MERSIImage.all_dts()):
    img = MERSIImage.from_dt(dt, "8")
    img.show_on_map(map_obj)

map_obj.show_in_browser()