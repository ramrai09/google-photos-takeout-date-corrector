import os
import json
import sys
from datetime import datetime
from pathlib import Path
import datetime
import re


stem_regex = r'.*\(\d+\)\..*'

date_from_file_name_regex_one = r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{3}'


def get_alike_regex(filename):
    tokens = filename.split(".")
    name = re.escape(".".join(tokens[0:len(tokens) - 1]))
    ext = re.escape(tokens[len(tokens) - 1])
    return fr".*{name}( (\d{{1,2}}\.){{2}}\d{{1,2}} PM)+\.{ext}\..*"


def get_alike_regex_with_duplication(filename):
    return fr".*{re.escape(filename)}( (\d{{1,2}}\.){{2}}\d{{1,2}} PM)+\..*"


def move_duplication_string(path):
    pattern = r"(.*)\((.*?)\)(\..*)"
    match = re.search(pattern, path)
    if match:
        new_path = match.group(1) + match.group(3) + "(" + match.group(2) + ")"
        return new_path
    else:
        return path


def get_alike_json(path):
    dir_path = os.path.dirname(path)
    file_name = os.path.basename(path)
    jsons = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.json')]
    regex = get_alike_regex(file_name)
    for json in jsons:
        if re.match(regex, json):
            return json

    # Try with duplication

    file_name = os.path.basename(move_duplication_string(path))
    regex = get_alike_regex_with_duplication(file_name)
    for json in jsons:
        if re.match(regex, json):
            return json


def get_json_data(image_path):
    json_path = Path(move_duplication_string(image_path) + ".json")
    json_data = None
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        try:
            with open(Path(image_path + ".json"), 'r') as f:
                json_data = json.load(f)
        except FileNotFoundError:
            try:
                # Remove the "-edited" from the file name
                no_edited = image_path.replace("-edited", "")
                with open(Path(no_edited + ".json"), 'r') as f:
                    json_data = json.load(f)
            except FileNotFoundError:
                try:
                    with open(Path(get_alike_json(image_path)), 'r') as f:
                        json_data = json.load(f)
                except FileNotFoundError:
                    print(f"Could not find JSON file for {image_path}")
                    return
                # os.remove(image_path)
    return json_data


def update_image_metadata(image_path):
    # Get the timestamp from the JSON file
    json_data = get_json_data(image_path)

    timestamp = json_data['photoTakenTime']['timestamp']
    # Convert the timestamp from string to float
    timestamp = float(timestamp)
    # Update the image's creation time
    os.utime(image_path, (timestamp, timestamp))

# def update_image_metadata_v2(image_path):
#     # Get year from folder name
#     folder_path = os.path.dirname(image_path)
#     folder_name = folder_path.split('/')[-1]
#     year_string = folder_name.split(' ')[-1]
#     if not year_string.isnumeric() or len(year_string) != 4:
#         return
#     # Convert year string to number, if it is
#     year = int(year_string)
#     last_day_of_year: datetime = datetime.datetime(year, 12, 31)
#     timestamp = last_day_of_year.timestamp()
#     # Update the image's creation time
#     os.utime(image_path, (timestamp, timestamp))


def update_image_metadata_v2(image_path):
    file_name = image_path.split('/')[-1]
    pattern = date_from_file_name_regex_one
    match = re.search(pattern, file_name)
    if match:
        date_time_array = match.group().split("-")
        year = int(date_time_array[0])
        month = int(date_time_array[1])
        day = int(date_time_array[2])
        hour = int(date_time_array[3])
        minute = int(date_time_array[4])
        second = int(date_time_array[5])
        corrected_datetime: datetime = datetime.datetime(year, month, day, hour, minute, second)
        timestamp = corrected_datetime.timestamp()
        # Update the image's creation time
        os.utime(image_path, (timestamp, timestamp))
    else:
        print("Could  update image creation time for " + file_path)


path = sys.argv[1]

for dirpath, dirnames, filenames in os.walk(path):
    for filename in filenames:
        if not filename.endswith('.json') and filename != '.DS_Store':
            file_path = os.path.join(dirpath, filename)
            # folder_path = os.path.dirname(file_path)
            # folder_name = folder_path.split('/')[-1]
            # year_string = folder_name.split(' ')[-1]
            # if not year_string.isnumeric() or len(year_string) != 4:
            #     continue
            try:
                update_image_metadata(file_path)
            except:
                update_image_metadata_v2(file_path)
