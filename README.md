# Photo GPS approximator

Small script to approximate gps data for files without gps exif data based on files with gps exif data.

The Issue:
Some images taken e.g. by old cameras do not have gps exif stored. But changes are good, that e.g. one used it's mobilephone for taking pictures at the (nearly) same time / same location too and this images do have location infos stored alongside them.
This script takes in two image collections, one as base of images with gps exif data, and one to process, the images without gps exif data.
It than tries to match images from one collection to images from the other, based on their date. It will find the base image with the smallest time delta (up to 14 days +-, can be adjusted in the code) and adds its gps data to the image without.

How it works:
* load base collection of images with gps exif data
* load process collection of images without gps exif data
* for each image in the process collection, the datetime wise nearest neighbour of the base collection is searched
* the gps data from this neighbour is added to the image from the process collection
* (hardcoded bound: if no base image is found in +-14days, no gps data will be added)

## usage

```
python3 gps_approximator.py [base_collection] [process_collection] [--dry_run]
        base_collection: glob to determine the base collection images
        process_collection: glob to determine the images to process
        --dry_run (optional): do not actualy modify the images, just show matches
```

### examples

```
python gps_approximator.py "base_data/*.jpeg" "process_data/*.jpeg"
```

Dryrun
```
python gps_approximator.py "base_data/*.jpeg" "process_data/*.jpeg" --dry
```
