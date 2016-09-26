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

# variables
url = 'https://api.weather.com/v1/geocode/'
plugin_conf = conf['plugins']['sensors']['weatherchannel']

# poll the sensor
def poll(sensor):
	request = sensor['plugin']['request']
	if request == "alerts":
		# request the web page
		return utils.web_get(url+str(plugin_conf['latitude'])+'/'+str(plugin_conf['longitude'])+'/'+get_request_type(sensor['plugin']['request'])+'/wwir.json?apiKey='+plugin_conf['api_key']+'&units=m&language=en')

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
	location = str(plugin_conf['latitude'])+"_"+str(plugin_conf['longitude'])+"_"
	return location+get_request_type(sensor['plugin']['request'])
