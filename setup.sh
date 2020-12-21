#!/bin/bash
set -evo pipefail

sudo apt update
sudo apt install -y virtualenv
pip2 install --upgrade virtualenv
virtualenv --python=python2.7 venv
source venv/bin/activate
source /opt/ros/melodic/setup.bash
pip2 install -r requirements.txt