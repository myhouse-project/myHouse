#!/usr/bin/python
##
# Sensor for: Weatherunderground
# args: [<latitude>/<longitude>]
# measures: temperature,weather_condition,temperature_record:day:min,temperature_record:day:max,temperature_normal:day:min,temperature_normal:day:max,forecast

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

# poll the sensor
def poll(sensor):
	# request the web page with lat,lon as parameter
	location = sensor["args"][0]
	return utils.get(url+cache_schema(sensor["type"])+"/q/"+location+".json")

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["type"] = sensor["type"]
	# parse the json
	parsed_json = json.loads(data)
	if sensor["type"] == "temperature": measure["value"] = parsed_json['current_observation']['temp_c']
	elif sensor["type"] == "weather_condition": measure["value"] = parsed_json['current_observation']['icon']
	elif sensor["type"] == "weather_forecast": 
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
		measure["value"] = json.dumps(forecast)
	elif sensor["type"] == "temperature_record": 
		measure_min = {}
		measure_min["type"] = sensor["type"]+":day:min"
		measure_min["value"] =  parsed_json['almanac']['temp_low']['record']['C']
		measures.append(measure_min)
		measure["type"] = sensor["type"]+":day:max"
		measure["value"] =  parsed_json['almanac']['temp_high']['record']['C']
	elif sensor["type"] == "temperature_normal":
		measure_min = {}
                measure_min["type"] = sensor["type"]+":day:min"
                measure_min["value"] =  parsed_json['almanac']['temp_low']['normal']['C']
                measures.append(measure_min)
                measure["type"] = sensor["type"]+":day:max"
                measure["value"] =  parsed_json['almanac']['temp_high']['normal']['C']
	# append the measure and return it
	measures.append(measure)
	return measures


# return the cache schema
def cache_schema(type):
	# return the API to call
	if type == "temperature" or type == "weather_condition": return "conditions"
	elif type == "weather_forecast": return "forecast10day"
	elif type == "temperature_record" or type == "temperature_normal": return "almanac"
