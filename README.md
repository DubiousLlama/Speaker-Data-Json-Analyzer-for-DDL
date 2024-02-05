# Speaker Data Json Analyzer for DDL

## Overview 
Written for https://deliberation.stanford.edu/.

Drop the jsonparser in the same folder as any number of deliberation JSONs you would like to analyze for speaker data.
By default, it is configured to produce a xlsx workbook with two sheets: one catalouging the length of every speak instance in every group, and the other catalouging the total speaking times by speaker in every group.

votingparser was built more recently generate csv files containing data on how often each participant voted to move on, etc. It uses a more updated method that treats the json as a dictionary object rather than attempting to convert it into a dataframe prematurely.

## Troubleshooting
This is a python script that relies on the pandas package. If it isn't working, do the following:
 - Confirm that Python 3.9 or higher is installed on your system, along with the Python Standard Library (this comes included with your python installation on Windows).
 - Run the following command: `pip install pandas`
 
If that command throws an error, check that python is configured in your system PATH variable.
