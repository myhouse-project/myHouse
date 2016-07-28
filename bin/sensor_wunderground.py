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
	location = sensor["args"][0]
	return utils.get(url+schema(measure)+"/q/"+location+".json")

# parse the measure
def parse(sensor,measure,data):
	parsed_json = json.loads(data)
	if measure == "temperature": return parsed_json['current_observation']['temp_c']
	elif  measure == "condition": return parsed_json['current_observation']['icon']
	elif  measure == "forecast": 
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
