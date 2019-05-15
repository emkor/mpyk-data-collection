#!/usr/bin/env bash

echo "Starting mpyk in separate process..."
nohup mpyk --each 10 --utc --dir ~/mpk/data --log ~/mpk/mpyk.log &
echo "Done!"