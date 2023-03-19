#! /bin/bash

# Pull latest changes
git pull origin main

# Create virtual environment
python -m venv venv

pip install -r requirements.txt
python main.py
