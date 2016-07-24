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

url = 'https://api.weather.com/v1/geocode/'
url_suffix = '/wwir.json?apiKey='+config['modules']['weather']['weatherchannel_api_key']+'&units=m&language=en'

# read the measure
def read(sensor,measure):
	location = sensor["args"].replace(',','/')
	return utils.get(url+location+'/'+schema(measure)+url_suffix)

# parse the measure
def parse(sensor,measure,data):
	parsed_json = json.loads(data)
	if measure == "alerts": 
		if isinstance(parsed_json["forecast"]["precip_time_24hr"],basestring): return parsed_json["forecast"]["phrase"]
		else: return ""
	else: logger.error(measure+" not supported by "+__name__)


# return the cache schema
def schema(measure):
	if measure == "alerts": return "forecast"
	else: logger.error(measure+" not supported by "+__name__)
