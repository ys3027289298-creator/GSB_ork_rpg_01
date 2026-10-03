#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install it to run Ork RPG."
    exit 1
fi

# Run the game
python3 ork_main.py