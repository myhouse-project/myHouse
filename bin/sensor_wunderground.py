#!/usr/bin/python
##
# Sensor for: Weatherunderground
# args: [<latitude>/<longitude>]
# measures: temperature,condition,record:min,record:max,normal:min,normal:max,forecast

import sys
import os
import requests
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# define the url constants
url = 'http://api.wunderground.com/api/'+conf['modules']['weather']['wunderground_api_key']+'/'

# read the measure
def poll(sensor):
	# request the web page with lat,lon as parameter
	location = sensor["args"][0]
	return utils.get(url+schema(sensor["measure"])+"/q/"+location+".json")

# parse the measure
def parse(sensor,data):
	# parse the json
	parsed_json = json.loads(data)
	if sensor["measure"] == "temperature": return parsed_json['current_observation']['temp_c']
	elif sensor["measure"] == "condition": return parsed_json['current_observation']['icon']
	elif sensor["measure"] == "forecast": 
		# return a json array with the forecast for each day
		forecast = []
		for entry in parsed_json['forecast']['simpleforecast']['forecastday']:
			forecast_entry = {}
			forecast_entry["condition"] = entry["icon"]
			forecast_entry["temp_high"] = entry["high"]["celsius"]
			forecast_entry["temp_low"] = entry["low"]["celsius"]
			forecast_entry["day"] = entry["date"]["weekday"]+', '+str(entry["date"]["monthname"])+' '+str(entry["date"]["day"])+' '+str(entry["date"]["year"])
			forecast_entry["forecast"] = entry["conditions"]+'. '
			if (entry["pop"] > 0): forecast_entry["forecast"] = forecast_entry["forecast"] + 'Precip. '+str(entry["pop"])+'%. '
			if (entry["qpf_allday"]["mm"] > 0): forecast_entry["forecast"] = forecast_entry["forecast"] + 'Rain '+str(entry["qpf_allday"]["mm"])+' mm. '
			if (entry["snow_allday"]["cm"] > 0): forecast_entry["forecast"] = forecast_entry["forecast"] + 'Snow '+str(entry["snow_allday"]["cm"])+' cm. '
			forecast.append(forecast_entry)
		return json.dumps(forecast)
	elif sensor["measure"] == "record:min": return parsed_json['almanac']['temp_low']['record']['C']
	elif sensor["measure"] == "record:max": return parsed_json['almanac']['temp_high']['record']['C']
        elif sensor["measure"] == "normal:min": return parsed_json['almanac']['temp_low']['normal']['C']
	elif sensor["measure"] == "normal:max": return parsed_json['almanac']['temp_high']['normal']['C']
	else: log.error(sensor["measure"]+" not supported by "+__name__)


# return the cache schema
def cache_schema(measure):
	# return the API to call
	if measure == "temperature" or measure == "condition": return "conditions"
	elif measure == "forecast": return "forecast10day"
	elif measure == "record:min" or measure == "record:max" or measure == "normal:min" or measure == "normal:max": return "almanac"
	else: log.error(measure+" not supported by "+__name__)
