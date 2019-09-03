#!/usr/bin/env bash

set -e
CSV_DIR=$1

echo "Running MPK data archival job..."
source ~/mpk/mpyk-data-collection/b2.sh
b2 authorize-account ${B2_KEY_ID} ${B2_APP_KEY}
for f in $(find ${CSV_DIR} -name "*.csv" | grep -v $(date --iso-8601 --utc))
do
  echo "Archiving file $f ..."
  zip --junk-paths -7 "$f.zip" ${f}
  b2 upload-file --noProgress ${B2_BUCKET} "$f.zip" $(basename "$f.zip")
  rm ${f}
  rm "$f.zip"
done
echo "Done archiving stuff"

echo "Creating listing file..."
rm -f ./listing.csv
while :
do
  LISTING=$(b2 list-file-names mpk-wroclaw $NEXT_FILE)
  NEXT_FILE=$(echo $LISTING | jq '.nextFileName' | xargs) # xargs trims string
  echo $LISTING | jq '.files[]' | jq -r '"\(.fileName);\(.fileId);\(.contentLength);\(.uploadTimestamp)"' >> ./listing.csv
  echo "Added listing page, next file=$NEXT_FILE"
  if [ "$NEXT_FILE" == "null" ]; then
    break
  fi
done
LISTING_FILE_COUNT=$(wc -l ./listing.csv)
b2 upload-file --noProgress ${B2_BUCKET} "listing.csv" "listing.csv"
echo "Uploaded listing containing $LISTING_FILE_COUNT files!"