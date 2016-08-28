#!/usr/bin/python

import sys
import os

import utils
import logger
log = logger.get_logger(__name__)

# poll the sensor
def poll(sensor):
	sensor_id = sensor["args"][0]
	if sensor["request"] == "temperature":
		log.debug("Reading "+'/sys/bus/w1/devices/'+sensor_id+'/w1_slave')
		# read and return the value from the sensor
	        with open('/sys/bus/w1/devices/'+sensor_id+'/w1_slave', 'r') as content_file:
			return content_file.read()

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	if sensor["request"] == "temperature":
		# retrieve and convert the temperature
		start = data.find("t=")
	        measure["value"] = float(data[start+2:start+7])/1000
	# append the measure and return it
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	if sensor['request'] == "temperature": return "temperature"

