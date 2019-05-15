# mpyk-data-collection
Scripts for collecting public transportation data for Wroclaw; made to run on Raspbian

## prerequisites
- `Raspbian`, `python>=3.5` installed
- `B2_KEY_ID`, `B2_APP_KEY`, and `B2_BUCKET` environment variables set for [backblaze b2 bucket](https://www.backblaze.com/)

## usage
- `setup.sh` installs OS dependencies and `mpyk`
- `start.sh` starts `mpyk` in separate process
- `zip_and_upload.sh <CSV DIR>` must be run daily, preferably using `cron`-job