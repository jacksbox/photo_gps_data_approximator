# Photo GPS approximator

Small script to approximate gps data for files without gps exif data based on files with gps exif data.

How it works:
* base collection of images with gps exif data
* process collection of images without gps exif data
* for each image in the process collection, the datetime wise nearest neighbour of the base collection is searched
* the gps data from this neighbour is added to the image from the process collection
* (hardcoded bound: if no base image is found in +-14days, no gps data will be added)

## usage

```
python gps_approximator.py <base_collection_glob> <process_collection_glob> <optional: --dry>
```

`base_collection_glob`: defines the images which should be used as base to approximate gps positions.
This images need gps exif data.

`process_collection_glob`: images for which the gps exif data should be approximated (based on the base_data)

`--dry`: will enable dry run mode in which the process_images are not updated.

### examples

```
python gps_approximator.py "base_data/*.jpeg" "process_data/*.jpeg" --dry
```

Dryrun
```
python gps_approximator.py "base_data/*.jpeg" "process_data/*.jpeg" --dry
```
