
import re
import sys
import json

def read_json_to_list(file_path):
    # Open and read the JSON file    
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    # Convert all values to a list of strings
    string_list = []
    for value in data.values():
        if isinstance(value, list):
            string_list.extend(value)  # If it's a list, extend the main list with these items
        else:
            string_list.append(str(value))  # If it's not a list, convert it to a string and append
    return string_list