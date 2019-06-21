#!/usr/bin/env bash

set -e
CSV_DIR=$1

echo "Running MPK data archival job..."
source ~/mpk/mpyk-data-collection/b2.sh
b2 authorize-account ${B2_KEY_ID} ${B2_APP_KEY}
for f in $(find ${CSV_DIR} -name "*.csv" | grep -v $(date --iso-8601 --utc)); do echo "Archiving file $f ..." && zip "$f.zip" ${f} && b2 upload-file --noProgress ${B2_BUCKET} "$f.zip" $(basename "$f.zip") && rm ${f} && rm "$f.zip"; done
echo "Done archiving stuff"

echo "Creating listing file..."
b2 list-file-names mpk-wroclaw | jq '.files[]' | jq '[.fileName, .fileId, .contentLength, .uploadTimestamp]' | jq -r 'join(";")' > ./listing.csv
LISTING_FILE_COUNT=$(wc -l ./listing.csv)
b2 upload-file --noProgress ${B2_BUCKET} "listing.csv" "listing.csv"
rm "listing.csv"
echo "Done! Listing contains $LISTING_FILE_COUNT files"