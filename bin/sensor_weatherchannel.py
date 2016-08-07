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

# poll the sensor
def poll(sensor):
	if sensor["type"] == "weather_alerts":
		# covert from lat,lon into lat/lon
		location = sensor["args"][0].replace(',','/')
		# request the web page
		return utils.get(url+location+'/'+cache_schema(sensor["type"])+url_suffix)

# parse the data
def parse(sensor,data):
	measures = []
        measure = {}
        measure["type"] = sensor["type"]
	# parse the json 
	parsed_json = json.loads(data)
	if sensor["type"] == "weather_alerts": 
		# return the alert
		alert = ""
		if isinstance(parsed_json["forecast"]["precip_time_24hr"],basestring): alert = parsed_json["forecast"]["phrase"]
		measure["value"] = alert
	# append the measure and return it
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(type):
	if type == "weather_alerts": return "forecast"
