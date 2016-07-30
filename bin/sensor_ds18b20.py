#!/usr/bin/python
##
# Sensor for DS18B20
# args: [<latitude>,<longitude>]
# measures: temperature

import sys
import os

import utils
import logger
log = logger.get_logger(__name__)

# read the measure
def poll(sensor):
	if sensor["measure"] == "temperature":
		sensor_id = sensor["args"][0]
		log.debug("Reading "+'/sys/bus/w1/devices/'+sensor_id+'/w1_slave')
		# read and return the value from the sensor
	        with open('/sys/bus/w1/devices/'+sensor_id+'/w1_slave', 'r') as content_file:
			return content_file.read()
	else: log.error(sensor["measure"]+" not supported by "+__name__)

# parse the measure
def parse(sensor,data):
	if sensor["measure"] == "temperature":
		# retrieve and convert the temperature
		start = data.find("t=")
	        return float(data[start+2:start+7])/1000
	else: log.error(sensor["measure"]+" not supported by "+__name__)

# return the cache schema
def cache_schema(measure):
	return measure

