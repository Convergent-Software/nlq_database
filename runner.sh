#!/bin/bash

# First, run 'chmod +x runner.sh'.
# Then, run './runner.sh app' to run the Streamlit app
# or './runner.sh seed' to run the seeder script.

if [ "$1" == "app" ]; then
    streamlit run app.py
elif [ "$1" == "seed" ]; then
    python setup.py
elif [ "$1" == "format" ]; then
    black .
else
    echo "Please use one of the following commands:"
    echo "'app' to run the Streamlit app"
    echo "'format' to format the code with Black"
    echo "'seed' to run the seeder script"
fi