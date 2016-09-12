#!/usr/bin/python

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
	request = sensor['plugin']['request']
	if request == "alerts":
		# request the web page
		return utils.web_get(url+str(conf['plugins']['weatherchannel']['latitude'])+'/'+str(conf['plugins']['weatherchannel']['longitude'])+'/'+get_request_type(sensor['plugin']['request'])+'/wwir.json?apiKey='+conf['plugins']['weatherchannel']['api_key']+'&units=m&language=en')

# parse the data
def parse(sensor,data):
	request = sensor['plugin']['request']
	measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
	# parse the json 
	parsed_json = json.loads(data)
	if request == "alerts": 
		# return the alert
		alert = ""
		if isinstance(parsed_json["forecast"]["precip_time_24hr"],basestring): alert = parsed_json["forecast"]["phrase"]
		measure["value"] = alert
	# append the measure and return it
	measures.append(measure)
        return measures

# return the plugin request type
def get_request_type(request):
        if request == "alerts": return "forecast"

# return the cache schema
def cache_schema(sensor):
	location = str(conf['plugins']['wunderground']['latitude'])+"_"+str(conf['plugins']['wunderground']['longitude'])+"_"
	return location+get_request_type(sensor['plugin']['request'])