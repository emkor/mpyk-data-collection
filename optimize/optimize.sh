#!/usr/bin/env bash

set -e
TMP_DIR=$1

mkdir -p $TMP_DIR
b2 authorize-account ${B2_KEY_ID} ${B2_APP_KEY}
for REMOTE_ZIP in $(cat "listing.csv")
do
  echo "Downloading $REMOTE_ZIP"
  b2 download-file-by-name --noProgress ${B2_BUCKET} $REMOTE_ZIP $REMOTE_ZIP

  echo "Extracting $REMOTE_ZIP"
  unzip $REMOTE_ZIP -d $TMP_DIR
  LOCAL_ZIP_NAME="pre_opt_$REMOTE_ZIP"
  mv $REMOTE_ZIP $LOCAL_ZIP_NAME
  for LOCAL_CSV in $(find $TMP_DIR -name "*.csv")
  do
    BEFORE_CSV_NAME="pre_opt_$(basename $LOCAL_CSV)"
    TARGET_CSV_NAME="$(basename $LOCAL_CSV)"
    echo "Moving $LOCAL_CSV -> $BEFORE_CSV_NAME"
    mv $LOCAL_CSV $BEFORE_CSV_NAME
    echo "Optimizing $LOCAL_CSV"
    ./optimize_csv.py $BEFORE_CSV_NAME $TARGET_CSV_NAME

    TARGET_ZIP_NAME="$TARGET_CSV_NAME.zip"
    echo "Compressing $TARGET_CSV_NAME into $TARGET_ZIP_NAME"
    zip -9 -j $TARGET_ZIP_NAME $TARGET_CSV_NAME

    echo "Uploading $TARGET_ZIP_NAME to B2"
    b2 upload-file --noProgress ${B2_BUCKET} $TARGET_ZIP_NAME $TARGET_ZIP_NAME

    rm -f $LOCAL_ZIP_NAME
    rm -f $BEFORE_CSV_NAME
    rm -rf $TMP_DIR
    rm -f $TARGET_CSV_NAME
    rm -rf $TARGET_ZIP_NAME
    echo "Done with $TARGET_CSV_NAME"
  done
done

echo "Done"