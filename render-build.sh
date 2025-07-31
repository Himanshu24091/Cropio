#!/usr/bin/env bash
# exit on error
set -o errexit

# Install the system dependencies required by PyMuPDF
apt-get update && apt-get install -y libgl1-mesa-glx

# Run your standard build command
pip install -r requirements.txt
