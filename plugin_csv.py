#!/usr/bin/python
import datetime
import time
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

plugin_conf = conf['plugins']['csv']

# poll the sensor
def poll(sensor):
	# read and return the content of file (in json)
	filename = sensor["plugin"]["csv_file"] if "csv_file" in sensor["plugin"] else plugin_conf['csv_file']
	with open(filename) as file:
		data = json.dumps(file.readlines())
	file.close()
	return data

# parse the data
def parse(sensor,data):
        measures = []
        measure = {}
	# load the file
	data = json.loads(data)
	# for each line
	for line in data:
		entry = line.split(',')
		measure = {}
		# if a node_id is defined, filter based on it
		if "node_id" in sensor["plugin"] and entry[sensor["plugin"]["node_id_index"+1]] != sensor["plugin"]["node_id"]: continue
		# if a measure prefix is defined, filter based on it
		if "measure" in sensor["plugin"] and not entry[sensor["plugin"]["measure_index"+1]].startswith(sensor['plugin']['measure']): continue
		# generate the timestamp
		if "date_index" in sensor["plugin"]:
			date = datetime.datetime.strptime(entry[sensor["plugin"]["date_index"+1]],sensor["plugin"]["date_format"])
			measure["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
		else: measure["timestamp"] = utils.now()
		# set the key as the sensor_id
		measure["key"] = sensor["sensor_id"]
		# strip out the measure from the value
		value = entry[sensor["plugin"]["measure_index"+1]]
		# if a measure prefix was defined, remove it
		if "measure" in sensor["plugin"]: value.replace(sensor['plugin']['measure'],"")
		# set the value
		measure["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
		measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	# cache the entire file
	filename = sensor["plugin"]["csv_file"] if "csv_file" in sensor["plugin"] else plugin_conf['csv_file']
	return filename

