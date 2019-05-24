#!/usr/bin/env bash

echo "Starting mpyk in separate process..."
source ~/mpk/mpyk-data-collection/b2.sh
nohup mpyk --each 15 --utc --dir ~/mpk/data --log ~/mpk/log/mpyk.log &
echo "Done!"