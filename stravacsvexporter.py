import argparse
import requests
import json
from datetime import datetime

PAGE_SIZE = 50
BASE_URL = "https://www.strava.com/api/v3/"
STREAM_CHOICES = ["time", "latlng", "distance", "altitude", "velocity_smooth", "heartrate", "cadence", "watts", "temp", "moving", "grade_smooth"]

# Converts a datetime into Unix Epoch format.
def to_epoch(orig_datetime):
    return (orig_datetime - datetime(1970,1,1)).total_seconds()

# Perform a GET requests and returns the result as JSON.
def get_json(url, access_token, querystr = {}):
    response = requests.get(url, querystr, headers={"Authorization": f"Bearer {access_token}"})
    return response.json()

# Gets all Strava activities.
def get_all_activities(access_token, after):
    result = []
    page = 1
    current_activities = []

    while len(current_activities) > 0 or page == 1:
        print("Getting activities page %i." % page)
        url = BASE_URL + "athlete/activities"
        current_activities = get_json(url, access_token, { "after": to_epoch(after), "per_page": PAGE_SIZE, "page": page })
        result = result + current_activities
        page += 1

    return result

# Gets the detail of a specified activity.
def get_activity_detail(access_token, id):
    print("Getting activity detail %i." % id)
    url = BASE_URL + "activities/%i" % id
    return get_json(url, access_token)

# Gets one or more streams.
def get_streams(access_token, activity_id, streams):
    print("Getting streams for activity %i." % activity_id)
    joined_streams = ",".join([x for x in streams])
    url = BASE_URL + "activities/%s/streams/%s?series_type=time" % (activity_id, joined_streams)
    return get_json(url, access_token)

# Parses the commandline arguments.
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-access_token", help = "The access-token used to authenticate with the Strava API.", required = True)
    parser.add_argument("-after", help = "The result will start with activities whose start_date is after this value, sorted oldest first.", required = True)
    parser.add_argument("-streams", help = "The streams to include in the result. Available stream: ", choices = STREAM_CHOICES, nargs = "*", required = False)
    parser.add_argument("-output", help = "The output file.", required = False, default = "output.json")
    return parser.parse_args()

args = parse_args()

# The date-string is parsed as a datetime object.
after = datetime.strptime(args.after, "%Y-%m-%d")

# We want to store the data is a json array. Each element represents an activity.
json_obj = []

activities = get_all_activities(args.access_token, after)

# Get the details of each activity and add them to the json array.
for activity in activities:
    detail = get_activity_detail(args.access_token, activity["id"])

    # If there are streams, get them and add them to the json object.
    if args.streams is not None:
        detail["streams"] = get_streams(args.access_token, activity["id"], args.streams)

    json_obj.append(detail)

with open(args.output, 'w') as outfile:
    json.dump(json_obj, outfile)
