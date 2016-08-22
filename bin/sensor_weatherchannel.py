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

# poll the sensor
def poll(sensor):
	api_key = sensor["args"][0]
	location = sensor["args"][1].replace(',','/')
	if sensor["request"] == "weather_alerts":
		# request the web page
		return utils.get(url+location+'/'+cache_schema(sensor["request"])+'/wwir.json?apiKey='+api_key+'&units=m&language=en')

# parse the data
def parse(sensor,data):
	measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
	# parse the json 
	parsed_json = json.loads(data)
	if sensor["request"] == "weather_alerts": 
		# return the alert
		alert = ""
		if isinstance(parsed_json["forecast"]["precip_time_24hr"],basestring): alert = parsed_json["forecast"]["phrase"]
		measure["value"] = alert
	# append the measure and return it
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(request):
	if request == "weather_alerts": return "forecast"
