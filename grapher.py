import time
import json
import pandas as pd
import numpy as np
import dateutil.parser
import datetime
import matplotlib.pyplot as plt

COLUMNS = ["id","name","tz0","tz1","tz2","tz3","tz4","tz5","trimp","fitness","fatigue","p"]
HR_MAX = 192
R1 = 60
R2 = 5
K1 = 0.0076
K2 = 0.0020

def get_stream(data, stream):
    streams = data["streams"]
    matches = list(filter(lambda s: s["type"] == stream, streams))

    if len(matches) == 0:
        raise ValueError("Unable to find stream %s." % stream)

    return matches[0]["data"]

def get_zone(value):
    percentage = (value * 100) / HR_MAX
    if percentage >= 50 and percentage < 60: return 1
    if percentage >= 60 and percentage < 70: return 2
    if percentage >= 70 and percentage < 80: return 3
    if percentage >= 80 and percentage < 90: return 4
    if percentage >= 90: return 5
    return 0

def process_activity(data_frame, activity):
    # Get the time and heartrate streams and store them in a series object.
    time_stream = get_stream(activity, "time")
    hr_stream = get_stream(activity, "heartrate")
    series = pd.Series(hr_stream, index = time_stream)

    # Remove duplicates. They break reindexing.
    series = series.drop_duplicates()

    # Add missing values. Missing values are constructed using linear interpolation (HR goes from 155 to 159 with in-between steps --> 155, 156, 157, 158, 159).
    series = series.reindex(range(max(time_stream)))
    series = series.interpolate(method = "linear")

    # Calculate HR zones.
    series = series.apply(get_zone)
    grouped = series.groupby(series.values)
    agg = grouped.aggregate(lambda x: len(x) / 60)  # Divide by 60 to get minutes.

    # Put the values in the row.
    activity_date = dateutil.parser.parse(activity["start_date"]).date()
    row = data_frame.loc[activity_date]

    row["id"] = activity["id"]
    row["name"] = activity["name"]

    for key in range(0, 6):
        row_key = "tz%i" % key
        current = row[row_key]
        tz = agg[key] if key in agg else 0
        row[row_key] = (current if not pd.isnull(current) else 0) + tz # If there is a current value, add it to the time in zone (multiple trainings a day).

def calculate_performance(data_frame):
    fitness = 0
    fatigue = 0
    for index, row in data_frame.copy().iterrows():
        fitness = fitness * np.exp(-1/R1) + row["trimp"];
        fatigue = fatigue * np.exp(-1/R2) + row["trimp"];
        data_frame.loc[index, "fitness"] = fitness
        data_frame.loc[index, "fatigue"] = fatigue

# Read and parse the json file.
with open("output.json") as data_file:    
    data = json.load(data_file)

# Create a dataframe to store our data in.
start_date = dateutil.parser.parse(data[0]["start_date"]).date() # We want to get the date without time.
end_date = datetime.date.today()
date_range = pd.date_range(start_date, end_date)
data_frame = pd.DataFrame(index = pd.DatetimeIndex(date_range), columns = COLUMNS)

# Process each activity in the json array.
for activity in data:
    process_activity(data_frame, activity)

# We don't want NaN in the dataframe. It messes up our calculations.
data_frame.fillna(0, inplace = True)

# Calculate trimp, fitness, fatigue and performance.
data_frame["trimp"] = data_frame["tz1"] + (2 * data_frame["tz2"]) + (3 * data_frame["tz3"]) + (4 * data_frame["tz4"]) + (5 * data_frame["tz5"])

calculate_performance(data_frame)

data_frame["p"] = K1 * data_frame["fitness"] - K2 * data_frame["fatigue"]

# Plot the results.
data_frame[["fitness","fatigue","p"]].plot()
plt.show()
