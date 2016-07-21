#!/usr/bin/python
import sys
import os
import requests
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../")
import core
logger = core.get_logger(__name__)
config = core.get_config()

url = 'http://api.wunderground.com/api/'+config["weather_wunderground_api_key"]+'/'

def read(sensor,measure):
	location = sensor["args"]
	if measure == "temperature" or measure == "condition":
		return core.get_json(url+"conditions/q/"+location+".json")
	else: logger.error(measure+" not supported by "+__name__)	


def parse(sensor,measure,data):
	parsed_json = json.loads(data)
	if measure == "temperature": return parsed_json['current_observation']['temp_c']
	elif  measure == "condition": parsed_json['current_observation']['icon']

def cache(measure):
	if measure == "temperature" or measure == "condition": return "conditions"

