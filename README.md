# mpyk-data-collection
Scripts for collecting public transportation data for Wroclaw; made to run on Raspbian

## prerequisites
- `Raspbian`, `python>=3.5` installed
- `B2_KEY_ID`, `B2_APP_KEY`, and `B2_BUCKET` environment variables set for [backblaze b2 bucket](https://www.backblaze.com/) in `b2.sh`

## usage
- `setup.sh` installs OS dependencies and `mpyk`
- `start.sh` starts `mpyk` in separate process; it should be in `cron`
- `zip_and_upload.sh <CSV DIR>` must be run daily, preferably using `cron`-job
- the `crontab` may look like this (`crontab -e`): 
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games`
    - `0 1 * * * /home/pi/mpk/mpyk-data-collection/zip_and_upload.sh /home/pi/mpk/data 1> /home/pi/mpk/log/zip_and_upload.log 2> /home/pi/mpk/log/zip_and_upload.err`
    - `@reboot /home/pi/mpk/mpyk-data-collection/start.sh 1> /home/pi/mpk/log/start.log 2> /home/pi/mpk/log/start.err`
