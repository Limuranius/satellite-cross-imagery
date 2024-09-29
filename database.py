import csv
import datetime

from Info import Info

with open("data.csv") as csvfile:
    reader = csv.reader(csvfile)
    data = [*reader]
    data = [i for i in data if i]
    data_dict = dict()
    for line in data:
        if line:
            data_dict[datetime.datetime.fromisoformat(line[8])] = line

with open("invalid.txt") as file:
    invalid = set([datetime.datetime.fromisoformat(date) for date in file.read().split()])


def parse_line(line) -> Info:
    return Info(
        (float(line[0]), float(line[1])),
        (float(line[2]), float(line[3])),
        (float(line[4]), float(line[5])),
        (float(line[6]), float(line[7])),
        datetime.datetime.fromisoformat(line[8]),
        "FY-3D"
    )


def to_line(info: Info):
    return [
        info.p1[0], info.p1[1],
        info.p2[0], info.p2[1],
        info.p3[0], info.p3[1],
        info.p4[0], info.p4[1],
        info.dt.isoformat(),
    ]


def get_by_dt(dt: datetime.datetime) -> Info | None:
    return parse_line(data_dict.get(dt))


def add_info(info: Info):
    data.append(to_line(info))
    with open("data.csv", "w", newline="") as file:
        csv.writer(file).writerows(data)


def add_invalid(dt: datetime.datetime):
    invalid.add(dt)
    with open("invalid.txt", "w") as file:
        file.write("\n".join([date.isoformat() for date in invalid]))


def has_dt(dt: datetime.datetime):
    return dt in data_dict


def has_invalid(dt: datetime.datetime):
    return dt in invalid