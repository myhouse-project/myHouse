#!/usr/bin/python
import sys
import os
import requests
import json

import utils
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()

url = 'http://api.wunderground.com/api/'+config['modules']['weather']['wunderground_api_key']+'/'

# read the measure
def read(sensor,measure):
	location = sensor["args"]
	return utils.get(url+schema(measure)+"/q/"+location+".json")

# parse the measure
def parse(sensor,measure,data):
	parsed_json = json.loads(data)
	if measure == "temperature": return parsed_json['current_observation']['temp_c']
	elif  measure == "condition": return parsed_json['current_observation']['icon']
	elif  measure == "forecast": return data
	elif  measure == "record:min": return parsed_json['almanac']['temp_low']['record']['C']
	elif  measure == "record:max": return parsed_json['almanac']['temp_high']['record']['C']
        elif  measure == "normal:min": return parsed_json['almanac']['temp_low']['normal']['C']
	elif  measure == "normal:max": return parsed_json['almanac']['temp_high']['normal']['C']
	else: logger.error(measure+" not supported by "+__name__)


# return the cache schema
def schema(measure):
	if measure == "temperature" or measure == "condition": return "conditions"
	elif measure == "forecast": return "forecast10day"
	elif measure == "record:min" or measure == "record:max" or measure == "normal:min" or measure == "normal:max": return "almanac"
	else: logger.error(measure+" not supported by "+__name__)
