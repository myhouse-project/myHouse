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

# define the url constants
url = 'http://api.wunderground.com/api'

# forecast max entris
forecast_max_entries = 5

# poll the sensor
def poll(sensor):
	# request the web page with lat,lon as parameter
	api_key = sensor["args"][0]
	location = sensor["args"][1]
	return utils.web_get(url+"/"+api_key+"/"+cache_schema(sensor)+"/q/"+location+".json")

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	# parse the json
	parsed_json = json.loads(data)
	if sensor["request"] == "temperature": 
		measure["value"] = parsed_json['current_observation']['temp_c']
		measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
		measures.append(measure)
	elif sensor["request"] == "condition": 
		measure["value"] = parsed_json['current_observation']['icon']
		measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
		measures.append(measure)
	elif sensor["request"] == "forecast_condition":
		for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
			measure = {}
			measure["key"] = sensor["sensor_id"]+":day:avg"
			measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
			measure["value"] = entry["icon"]
			measures.append(measure)
        elif sensor["request"] == "forecast_pop":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["pop"] if entry["pop"] > 0 else 0
                        measures.append(measure)
        elif sensor["request"] == "forecast_rain":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["qpf_allday"]["mm"] if entry["qpf_allday"]["mm"] > 0 else 0
                        measures.append(measure)
        elif sensor["request"] == "forecast_snow":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["snow_allday"]["cm"] if entry["snow_allday"]["cm"] > 0 else 0
                        measures.append(measure)
        elif sensor["request"] == "forecast_temperature":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
	                measure["key"] = sensor["sensor_id"]+":day:min"
        	        measure["value"] =  utils.normalize(entry["low"]["celsius"])
	                measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
	                measures.append(measure)
	                measure = {}
	                measure["key"] = sensor["sensor_id"]+":day:max"
	                measure["value"] =  utils.normalize(entry["high"]["celsius"])
	                measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
	                measures.append(measure)
	elif sensor["request"] == "temperature_record": 
		measure["key"] = sensor["sensor_id"]+":day:min"
		measure["value"] =  parsed_json['almanac']['temp_low']['record']['C']
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
		measure = {}
		measure["key"] = sensor["sensor_id"]+":day:max"
		measure["value"] =  parsed_json['almanac']['temp_high']['record']['C']
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
	elif sensor["request"] == "temperature_normal":
                measure["key"] = sensor["sensor_id"]+":day:min"
                measure["value"] =  parsed_json['almanac']['temp_low']['normal']['C']
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
		measure = {}
                measure["key"] = sensor["sensor_id"]+":day:max"
                measure["value"] =  parsed_json['almanac']['temp_high']['normal']['C']
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
	# append the measure and return it
	return measures


# return the cache schema
def cache_schema(sensor):
	# return the API to call
	if sensor['request'] == "temperature" or sensor['request'] == "condition": return "conditions"
	elif sensor['request'].startswith("forecast_"): return "forecast10day"
	elif sensor['request'] == "temperature_record" or sensor['request'] == "temperature_normal": return "almanac"
