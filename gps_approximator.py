import math
import logging
import sys
import pyexiv2
from typing import List, TypedDict, Union
from datetime import datetime
from glob import glob
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


DATE_FIELD = "Exif.Photo.DateTimeOriginal"
GPS_LAT_FIELD = "Exif.GPSInfo.GPSLatitude"
GPS_LONG_FIELD = "Exif.GPSInfo.GPSLongitude"
GPS_ALT_FIELD = "Exif.GPSInfo.GPSAltitude"

MAX_DIFF_DAYS = 14


class Coordinates():
    lat: str
    long: str


class PhotoData(TypedDict):
    file: str
    date: str
    datetime: datetime
    gps: Union[Coordinates, None]


def get_datetime(date: str) -> datetime:
    return datetime.strptime(date, "%Y:%m:%d %H:%M:%S")


def find_photos(path: str, with_gps=True) -> List[PhotoData]:
    photos = glob(path)
    photo_data = []
    for photo in photos:
        image = pyexiv2.Image(photo)
        data = image.read_exif()
        image.close()
        gps_data = (
            {GPS_LAT_FIELD: data[GPS_LAT_FIELD], GPS_LONG_FIELD: data[GPS_LONG_FIELD]}
            if GPS_LAT_FIELD in data and GPS_LONG_FIELD in data
            else None
        )
        if gps_data and GPS_ALT_FIELD in data:
            gps_data[GPS_ALT_FIELD] = data[GPS_ALT_FIELD]
        if not with_gps or (with_gps and gps_data):
            photo_data.append({
                "file": photo,
                "date": data[DATE_FIELD],
                "datetime": get_datetime(data[DATE_FIELD]),
                "gps": gps_data
            })

    return photo_data


# bindary search
def find_nearest(
    photo, photos_with_gps: List[PhotoData]
) -> PhotoData:
    min_index, max_index = 0, len(photos_with_gps) - 1
    match = None
    while match is None:
        diff = (max_index - min_index)
        if diff == 0:
            match = photos_with_gps[max_index]
        elif diff == 1:
            diff_max = abs(photos_with_gps[max_index]["datetime"] - photo["datetime"])
            diff_min = abs(photos_with_gps[min_index]["datetime"] - photo["datetime"])
            match = (
                photos_with_gps[max_index] if diff_max < diff_min
                else photos_with_gps[min_index]
            )
        else:
            mid_index = min_index + math.ceil(diff / 2)
            if photo["date"] == photos_with_gps[mid_index]["date"]:
                match = photos_with_gps[mid_index]
            elif photo["date"] > photos_with_gps[mid_index]["date"]:
                min_index = mid_index
            elif photo["date"] < photos_with_gps[mid_index]["date"]:
                max_index = mid_index

    return match


def in_bounds(date_a, date_b) -> bool:
    max_date = max(get_datetime(date_a), get_datetime(date_b))
    min_date = min(get_datetime(date_a), get_datetime(date_b))
    datetime_diff = max_date - min_date
    if datetime_diff.days > MAX_DIFF_DAYS:
        return False
    return True


def add_gps_to_photo(photo: PhotoData, gps):
    pass

def gps_approximator(base_path, process_path, dry_run):
    photos_with_gps = sorted(find_photos(base_path), key=lambda x: x['date'])
    pwg_len = len(photos_with_gps)
    logger.info(f"images as base:  {pwg_len}")
    if pwg_len == 0:
        raise Exception("No base images were found")

    photos_without_gps = find_photos(process_path, False)
    pwog_len = len(photos_without_gps)
    logger.info(f"images to process:  {pwog_len}")
    logger.debug("\n")
    if pwog_len == 0:
        raise Exception("No images to process were found")

    matched = []
    unmatched = []
    for current_photo, index in zip(photos_without_gps, range(pwog_len)):
        logger.debug(f"# processing {index + 1}/{pwog_len}")
        logger.debug(f"  file:  {current_photo['file']}")
        match = find_nearest(current_photo, photos_with_gps)
        if in_bounds(current_photo["date"], match["date"]):
            if not dry_run:
                add_gps_to_photo(current_photo, match["gps"])

            logger.debug(f"  match: {match['file']}")
            matched.append((current_photo, match))
        else:
            logger.debug("  unmatched")
            unmatched.append(current_photo)

    logger.debug("\n")
    logger.info(f"matched photos: {len(matched)}")
    logger.info(f"unmatched photos: {len(unmatched)}")


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3 or len(args) > 4:
        raise Exception("Usage: python.py gps_approximator.py <path_base> <bath_process> <optional: --dry>")

    dry_run = len(args) == 4 and args[3] == "--dry"

    gps_approximator(args[1], args[2], dry_run)
