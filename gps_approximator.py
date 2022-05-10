import math
import logging
import sys
import pyexiv2
from typing import List, TypedDict, Union
from datetime import datetime
from glob import glob

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


class ImageData(TypedDict):
    file: str
    date: str
    datetime: datetime
    gps: Union[Coordinates, None]


def get_datetime(date: str) -> datetime:
    return datetime.strptime(date, "%Y:%m:%d %H:%M:%S")


def find_images(path: str, with_gps=True) -> List[ImageData]:
    images = glob(path)
    image_data = []
    for image in images:
        exivimg = pyexiv2.Image(image)
        data = exivimg.read_exif()
        exivimg.close()
        gps_data = (
            {
                GPS_LAT_FIELD: data[GPS_LAT_FIELD],
                GPS_LONG_FIELD: data[GPS_LONG_FIELD]
            }
            if GPS_LAT_FIELD in data and GPS_LONG_FIELD in data
            else None
        )
        if gps_data and GPS_ALT_FIELD in data:
            gps_data[GPS_ALT_FIELD] = data[GPS_ALT_FIELD]
        if (not with_gps and not gps_data) or (with_gps and gps_data):
            image_data.append({
                "file": image,
                "date": data[DATE_FIELD],
                "datetime": get_datetime(data[DATE_FIELD]),
                "gps": gps_data
            })

    return image_data


# bindary search
def find_nearest(
    image, images_with_gps: List[ImageData]
) -> ImageData:
    min_index, max_index = 0, len(images_with_gps) - 1
    match = None
    while match is None:
        diff = (max_index - min_index)
        if diff == 0:
            match = images_with_gps[max_index]
        elif diff == 1:
            diff_max = abs(images_with_gps[max_index]["datetime"] - image["datetime"])
            diff_min = abs(images_with_gps[min_index]["datetime"] - image["datetime"])
            match = (
                images_with_gps[max_index] if diff_max < diff_min
                else images_with_gps[min_index]
            )
        else:
            mid_index = min_index + math.ceil(diff / 2)
            if image["date"] == images_with_gps[mid_index]["date"]:
                match = images_with_gps[mid_index]
            elif image["date"] > images_with_gps[mid_index]["date"]:
                min_index = mid_index
            elif image["date"] < images_with_gps[mid_index]["date"]:
                max_index = mid_index

    return match


def in_bounds(date_a, date_b) -> bool:
    max_date = max(get_datetime(date_a), get_datetime(date_b))
    min_date = min(get_datetime(date_a), get_datetime(date_b))
    datetime_diff = max_date - min_date
    if datetime_diff.days > MAX_DIFF_DAYS:
        return False
    return True


def add_gps_to_image(image: ImageData, gps):
    exivimg = pyexiv2.Image(image["file"])
    exivimg.modify_exif(gps)
    exivimg.close()


def gps_approximator(base_path, process_path, dry_run=False):
    images_with_gps = sorted(find_images(base_path), key=lambda x: x['date'])
    pwg_len = len(images_with_gps)
    logger.info(f"images as base:  {pwg_len}")
    if pwg_len == 0:
        logger.error("No base images were found")
        sys.exit(1)

    images_without_gps = find_images(process_path, False)
    pwog_len = len(images_without_gps)
    logger.info(f"images to process:  {pwog_len}")
    logger.debug("\n")
    if pwog_len == 0:
        logger.error("No images to process were found")
        sys.exit(1)

    matched = []
    unmatched = []
    failed = []
    for current_image, index in zip(images_without_gps, range(pwog_len)):
        logger.debug(f"# processing {index + 1}/{pwog_len}")
        logger.debug(f"  file:  {current_image['file']}")
        match = find_nearest(current_image, images_with_gps)
        if in_bounds(current_image["date"], match["date"]):
            if not dry_run:
                try:
                    add_gps_to_image(current_image, match["gps"])
                except Exception:
                    logger.exception(
                        f"Failed to add GPS data to images {current_image['file']}"
                    )
                    failed.append(current_image)

            logger.debug(f"  match: {match['file']}")
            matched.append((current_image, match))
        else:
            logger.debug("  unmatched")
            unmatched.append(current_image)

    logger.debug("\n")
    logger.info(f"matched images: {len(matched)}")
    logger.info(f"unmatched images: {len(unmatched)}")
    logger.info(f"failed images: {len(failed)}")


USAGE = """
Usage:
    python3 gps_approximator.py [base_collection] [process_collection] [--dry_run]
        base_collection: glob to determine the base collection images
        process_collection: glob to determine the images to process
        --dry_run (optional): do not actualy modify the images
"""

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3 or len(args) > 4:
        logger.error(f"Error: expected 2 or 3 parameters \n{USAGE}")
        sys.exit(1)

    dry_run = len(args) == 4 and args[3] == "--dry"

    gps_approximator(args[1], args[2], dry_run)
