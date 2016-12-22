#!/usr/bin/python
import datetime
import time
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

plugin_conf = conf['plugins']['fdsnws']
limit = 10000

# poll the sensor
def poll(sensor):
	# query the service
	url = "http://"+sensor["plugin"]["domain"]+"/fdsnws/event/1/query?format=text&limit="+limit+"&"+sensor["plugin"]["query"]
	data = utils.web_get(filename)
	return json.dumps(data)

# parse the data
def parse(sensor,data):
        measures = []
        measure = {}
	# load the file
	data = json.loads(data)
	# for each line
	for line in data:
		measure = {}
		entry = line.split('|')
		#EventID|Time|Latitude|Longitude|Depth/Km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName
		#    0    1      2          3       4       5     6           7            8           9     10         11           12
		date_format = "%Y-%m-%dT%H:%M:%S.%f"
		date = datetime.datetime.strptime(entry[1],date_format)
		# if a filter is defined, ignore the line if the filter is not found
		if "filter" in sensor["plugin"] and entry[sensor["plugin"]["filter_position"+1]] != sensor["plugin"]["filter"]: continue
		# if a prefix is defined, filter based on it
		if "prefix" in sensor["plugin"] and not entry[sensor["plugin"]["value_position"+1]].startswith(sensor['plugin']['prefix']): continue
		# generate the timestamp
		if "date_position" in sensor["plugin"]:
			date = datetime.datetime.strptime(entry[sensor["plugin"]["date_position"+1]],sensor["plugin"]["date_format"])
			measure["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
		else: measure["timestamp"] = utils.now()
		# set the key as the sensor_id
		measure["key"] = sensor["sensor_id"]
		# strip out the measure from the value
		value = entry[sensor["plugin"]["value_position"+1]]
		# if a measure prefix was defined, remove it
		if "prefix" in sensor["plugin"]: value.replace(sensor['plugin']['prefix'],"")
		# set the value
		measure["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
		measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	# cache the entire file
	filename = sensor["plugin"]["csv_file"] if "csv_file" in sensor["plugin"] else plugin_conf['csv_file']
	return filename

