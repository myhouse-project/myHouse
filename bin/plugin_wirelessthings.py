#!/usr/bin/python
import datetime
import time

import utils
import logger
import json
log = logger.get_logger(__name__)

# poll the sensor
def poll(sensor):
	# read and return the content of file (in json)
	with open(sensor['plugin']['file']) as file:
		return json.dumps(file.readlines())

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
		# split the values
		node_id = entry[1]
		value = entry[2]
		# skip if the entry is not related to the node_id and measure we are looking for
		if node_id != sensor['plugin']['node_id']: continue
		if not value.startswith(sensor['plugin']['measure']): continue
		# generate the timestamp
		date = datetime.datetime.strptime(entry[0],"%d %b %Y %H:%M:%S +0000")
		measure["timestamp"] = utils.timezone(int(time.mktime(date.timetuple())))
		measure["key"] = sensor["sensor_id"]
		# strip out the measure from the value
		measure["value"] = float(value.replace(sensor['plugin']['measure'],""))
		measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	# cache the entire file
	return sensor['plugin']['file']

