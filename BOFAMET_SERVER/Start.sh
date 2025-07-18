#!/bin/bash

echo "INFO: Initiating system update and package installation!"

sudo apt update && sudo apt upgrade -y
sudo apt install python3 -y
sudo apt install python3-pip -y

echo "INFO: Core dependencies installed. Now installing Python libraries!"

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "ERROR: requirements.txt not found! Cannot install Python libraries!"
    exit 1
fi

echo "INFO: All dependencies are satisfied! Launching Config_C2.py!"

python3 Config_C2.py

echo "INFO: Setup complete or initiated. Check server status." 