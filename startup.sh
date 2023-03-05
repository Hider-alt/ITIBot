#! /bin/bash

# Load .env file
set -o allexport
source .env
set +o allexport

git config --global user.password $GIT_PASSWORD
git clone https://github.com/Hider-alt/ITIBot
cd ITIBot
git fetch
git pull
pip install -r requirements.txt
python main.py
