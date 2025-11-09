#!/bin/bash

# INSTALL HOMEBREW
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# INSTALL FFMPEG
brew install ffmpeg
# CLONE PROJECT
git clone git@github.com:schwwaaa/videobeaux.git
# GO TO DIRECTORY
cd videobeaux
# CREATE VIRTUAL ENVIRONMENT
python3 -m venv env
# ACTIVATE VIRTUAL ENVIRONMENT
source env/bin/activate
# INSTALL DEPENDENCIES
pip install .