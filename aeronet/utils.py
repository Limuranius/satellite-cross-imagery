import datetime
import pandas as pd


def get_closest_value(target: int | float, values: list[int | float]):
    min_delta = abs(target - values[0])
    closest = values[0]
    for value in values:
        delta = abs(value - closest)
        if delta < min_delta:
            closest = value
            min_delta = delta
    return closest


def get_closest_date_data(df: pd.DataFrame, site: str, dt: datetime.datetime):
    site_data = df[df["Site"] == site]
    i = abs(site_data["Datetime"] - dt).argmin()
    row = site_data.loc[i]

    max_time_diff = datetime.timedelta(hours=3)
    assert abs(row["Datetime"] - dt) < max_time_diff
    return row
