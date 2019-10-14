#!/usr/bin/env bash

echo `date`

echo "Changing into ~/jaxa"
cd /home/uwcc-admin/jaxa
echo "Inside `pwd`"


# If no venv (python3 virtual environment) exists, then create one.
if [ ! -d "venv" ]
then
    echo "Creating venv python3 virtual environment."
    virtualenv -p python3 venv
fi

# Activate venv.
echo "Activating venv python3 virtual environment."
source venv/bin/activate

# Install dependencies using pip.
if [ ! -f "jaxa_rfield.log" ]
then
    echo "Installing pandas"
    pip install pandas
    echo "Installing urllib3"
    pip install urllib3
    touch jaxa_rfield.log
fi


# Create Jaxa rfield
echo "Running jaxa_rfield.py"
python jaxa_rfield.py >> jaxa_rfield.log 2>&1
# Deactivating virtual environment
echo "Deactivating virtual environment"
deactivate
