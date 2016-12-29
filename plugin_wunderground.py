#!/usr/bin/python
import sys
import os
import requests
import json
import datetime
import time

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
url = 'http://api.wunderground.com/api'
forecast_max_entries = 5
plugin_conf = conf['plugins']['wunderground']

# poll the sensor
def poll(sensor):
	# request the web page
        location = str(conf["general"]["latitude"])+","+str(conf["general"]["longitude"])
        if "location" in sensor["plugin"]: location = sensor["plugin"]["location"]
	return utils.web_get(url+"/"+plugin_conf['api_key']+"/"+get_request_type(sensor['plugin']['measure'])+"/q/"+location+".json")

# parse the data
def parse(sensor,data):
	request = sensor['plugin']['measure']
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	# parse the json
	parsed_json = json.loads(data)
	if request == "temperature": 
		measure["value"] = float(parsed_json['current_observation']['temp_c'])
		measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
		measures.append(measure)
	elif request == "humidity":
                measure["value"] = int(parsed_json['current_observation']['relative_humidity'].replace('%',''))
                measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
                measures.append(measure)
        elif request == "wind":
                measure["value"] = float(parsed_json['current_observation']['wind_kph'])
                measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
                measures.append(measure)
        elif request == "wind_gust":
                measure["value"] = float(parsed_json['current_observation']['wind_gust_kph'])
                measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
                measures.append(measure)
        elif request == "pressure":
                measure["value"] = float(parsed_json['current_observation']['pressure_mb'])
                measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
                measures.append(measure)
	elif request == "condition": 
		measure["value"] = parsed_json['current_observation']['icon']
		measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
		measures.append(measure)
        elif request == "wind_dir":
		direction = parsed_json['current_observation']['wind_dir']
		if len(direction) > 0 and (direction[0] == "N" or direction[0] == "W" or direction[0] == "S" or direction[0] == "E"): direction = direction[0]
		else: direction = "-"
                measure["value"] = direction
                measure["timestamp"] = utils.timezone(int(parsed_json['current_observation']['observation_epoch']))
                measures.append(measure)
	elif request == "forecast_condition":
		for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
			measure = {}
			measure["key"] = sensor["sensor_id"]+":day:avg"
			measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
			measure["value"] = entry["icon"]
			measures.append(measure)
        elif request == "forecast_pop":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["pop"] if entry["pop"] > 0 else 0
                        measures.append(measure)
        elif request == "forecast_rain":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["qpf_allday"]["mm"] if entry["qpf_allday"]["mm"] > 0 else 0
                        measures.append(measure)
        elif request == "forecast_snow":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
                        measure["key"] = sensor["sensor_id"]+":day:avg"
                        measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
                        measure["value"] = entry["snow_allday"]["cm"]*10 if entry["snow_allday"]["cm"] > 0 else 0
                        measures.append(measure)
        elif request == "forecast_temperature":
                for entry in parsed_json['forecast']['simpleforecast']['forecastday'][:forecast_max_entries]:
                        measure = {}
	                measure["key"] = sensor["sensor_id"]+":day:min"
        	        measure["value"] =  int(entry["low"]["celsius"])
	                measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
	                measures.append(measure)
	                measure = {}
	                measure["key"] = sensor["sensor_id"]+":day:max"
	                measure["value"] =  int(entry["high"]["celsius"])
	                measure["timestamp"] = utils.day_start(utils.timezone(int(entry["date"]["epoch"])))
	                measures.append(measure)
	elif request == "record_temperature": 
		measure["key"] = sensor["sensor_id"]+":day:min"
		measure["value"] =  int(parsed_json['almanac']['temp_low']['record']['C'])
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
		measure = {}
		measure["key"] = sensor["sensor_id"]+":day:max"
		measure["value"] =  int(parsed_json['almanac']['temp_high']['record']['C'])
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
        elif request == "record_temperature_year":
                measure["key"] = sensor["sensor_id"]+":day:min"
                measure["value"] =  int(parsed_json['almanac']['temp_low']['recordyear'])
                measure["timestamp"] = utils.day_start(utils.now())
                measures.append(measure)
                measure = {}
                measure["key"] = sensor["sensor_id"]+":day:max"
                measure["value"] =  int(parsed_json['almanac']['temp_high']['recordyear'])
                measure["timestamp"] = utils.day_start(utils.now())
                measures.append(measure)
	elif request == "normal_temperature":
                measure["key"] = sensor["sensor_id"]+":day:min"
                measure["value"] =  int(parsed_json['almanac']['temp_low']['normal']['C'])
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
		measure = {}
                measure["key"] = sensor["sensor_id"]+":day:max"
                measure["value"] =  int(parsed_json['almanac']['temp_high']['normal']['C'])
		measure["timestamp"] = utils.day_start(utils.now())
		measures.append(measure)
	elif request == "rain":
                measure["key"] = sensor["sensor_id"]+":day:avg"
		date_dict = parsed_json['history']['dailysummary'][0]['date']
                date = datetime.datetime.strptime(date_dict["mday"]+"-"+date_dict["mon"]+"-"+date_dict["year"],"%d-%m-%Y")
                measure["timestamp"] = utils.timezone(int(time.mktime(date.timetuple())))
                measure["value"] =  float(parsed_json['history']['dailysummary'][0]['precipm'])
                measures.append(measure)
        elif request == "snow":
                measure["key"] = sensor["sensor_id"]+":day:avg"
                date_dict = parsed_json['history']['dailysummary'][0]['date']
                date = datetime.datetime.strptime(date_dict["mday"]+"-"+date_dict["mon"]+"-"+date_dict["year"],"%d-%m-%Y")
                measure["timestamp"] = utils.timezone(int(time.mktime(date.timetuple())))
                measure["value"] = float(parsed_json['history']['dailysummary'][0]['precipm']) if utils.is_number(parsed_json['history']['dailysummary'][0]['precipm']) else 0
                measures.append(measure)
	else: log.warning("invalid measure requested: "+request)		
	# append the measure and return it
	return measures

# return the plugin request type
def get_request_type(request):
        if request == "temperature" or request == "pressure" or request == "condition" or request == "humidity" or request == "wind" or request == "wind_gust" or request == "wind_dir": return "conditions"
        elif request.startswith("forecast_"): return "forecast10day"
        elif request == "record_temperature" or request == "record_temperature_year" or request == "normal_temperature": return "almanac"
	elif request == "rain" or request == "snow": return "yesterday"

# return the cache schema
def cache_schema(sensor):
        location = str(conf["general"]["latitude"])+","+str(conf["general"]["longitude"])
        if "location" in sensor["plugin"]: location = sensor["plugin"]["location"]
	return location+"_"+get_request_type(sensor['plugin']['measure'])
