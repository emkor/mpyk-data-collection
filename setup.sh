#!/usr/bin/env bash

set -e

echo "Installing git..."
sudo apt-get install -y git zip curl

echo "Installing pip for Python 3..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

sudo pip install b2

-p ~/mpk/data && cd ~/mpk
git clone https://github.com/emkor/mpyk.git && cd mpyk
sudo pip install -r requirements.txt && chmod u+x mpyk.py

sudo ln -s ~/mpk/mpyk/mpyk.py /usr/local/bin/mpyk
