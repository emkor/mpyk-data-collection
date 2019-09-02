#!/usr/bin/env bash

set -e

echo "Installing OS deps..."
sudo apt-get update
sudo apt-get install -y git zip curl

echo "Installing pip for Python 3..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

sudo pip install b2

mkdir -p ~/mpk/log && mkdir -p ~/mpk/data && cd ~/mpk
git clone https://github.com/emkor/mpyk.git && cd ~/mpk/mpyk
sudo pip install -r requirements.txt && chmod u+x ~/mpk/mpyk/mpyk.py

sudo ln -s ~/mpk/mpyk/mpyk.py /usr/local/bin/mpyk
