#!/usr/bin/python
##
# Sensor for: Weather Channel
# args: [<latitude>,<longitude>]
# measures: alerts

import sys
import os
import requests
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# define constants
url = 'https://api.weather.com/v1/geocode/'
url_suffix = '/wwir.json?apiKey='+conf['modules']['weather']['weatherchannel_api_key']+'&units=m&language=en'

# read the measure
def poll(sensor):
	if sensor["measure"] == "weather_alerts":
		# covert from lat,lon into lat/lon
		location = sensor["args"][0].replace(',','/')
		# request the web page
		return utils.get(url+location+'/'+cache_schema(sensor["measure"])+url_suffix)
	else: log.error(sensor["measure"]+" not supported by "+__name__)

# parse the measure
def parse(sensor,data):
	# parse the json 
	parsed_json = json.loads(data)
	if sensor["measure"] == "weather_alerts": 
		# return the alert
		if isinstance(parsed_json["forecast"]["precip_time_24hr"],basestring): return parsed_json["forecast"]["phrase"]
		else: return ""
	else: log.error(sensor["measure"]+" not supported by "+__name__)


# return the cache schema
def cache_schema(measure):
	if measure == "weather_alerts": return "forecast"
	else: log.error(measure+" not supported by "+__name__)
