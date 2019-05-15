#!/usr/bin/env bash

set -e

CSV_DIR=$1

b2 authorize-account ${B2_KEY_ID} ${B2_APP_KEY}
for f in $(find ${CSV_DIR} -name "*.csv" | grep -v $(date --iso-8601 --utc)); do zip "$f.zip" ${f} && b2 upload-file --noProgress ${B2_BUCKET} "$f.zip" $(basename "$f.zip") && rm ${f} && rm "$f.zip"; done