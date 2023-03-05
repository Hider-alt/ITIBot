#! /bin/bash

# Load .env file
set -o allexport

git config --global user.password $GIT_PASSWORD
git clone https://github.com/Hider-alt/ITIBot

# Extract ITIBot folder content to root
cp -r ITIBot/* .
rm -rf ITIBot

git fetch
git pull

# Create virtual environment
python -m venv venv

pip install -r requirements.txt
python main.py
