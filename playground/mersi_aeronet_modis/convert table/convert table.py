import pandas

df = pandas.read_csv("../data_with_mersi.csv", sep="\t")

banned_cols = open("remove_cols.txt").read().strip().split()

df = df.drop(columns=banned_cols)

rename = {
    "nir_Lt_412_mean": "modis_Lt[412nm]",
    "nir_Lt_443_mean": "modis_Lt[443nm]",
    "nir_Lt_469_mean": "modis_Lt[469nm]",
    "nir_Lt_488_mean": "modis_Lt[488nm]",
    "nir_Lt_531_mean": "modis_Lt[531nm]",
    "nir_Lt_547_mean": "modis_Lt[547nm]",
    "nir_Lt_555_mean": "modis_Lt[555nm]",
    "nir_Lt_645_mean": "modis_Lt[645nm]",
    "nir_Lt_667_mean": "modis_Lt[667nm]",
    "nir_Lt_678_mean": "modis_Lt[678nm]",
    "nir_Lt_748_mean": "modis_Lt[748nm]",
    "nir_Lt_859_mean": "modis_Lt[859nm]",
    "nir_Lt_869_mean": "modis_Lt[869nm]",
    "nir_Lt_1240_mean": "modis_Lt[1240nm]",
    "nir_Lt_1640_mean": "modis_Lt[1640nm]",
    "nir_Lt_2130_mean": "modis_Lt[2130nm]",
}
df = df.rename(columns=rename)

df.to_csv("output.csv", sep="\t", index=False)
