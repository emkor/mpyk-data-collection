#!/usr/bin/env bash

echo "Starting mpyk in separate process..."
source ~/mpk/mpyk-data-collection/b2.sh
nohup mpyk --each 10 --utc --dir ~/mpk/data --log ~/mpk/log/mpyk.log
echo "Done!"