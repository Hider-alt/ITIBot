#! /bin/bash

# Load .env file
set -o allexport

git config --global user.password "$GIT_PASSWORD"
git clone https://github.com/Hider-alt/ITIBot

# Extract ITIBot folder content to root
cp -r ITIBot/* .
rm -rf ITIBot

# Set git origin (https://github.com/Hider-alt/ITIBot.git) if not set
git remote set-url origin

# Pull latest changes
git fetch
git pull

# Create virtual environment
python -m venv venv

pip install -r requirements.txt
python main.py
