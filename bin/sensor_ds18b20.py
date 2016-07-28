#!/usr/bin/python
import sys
import os

import utils
import logger
logger = logger.get_logger(__name__)

# read the measure
def read(sensor,measure):
	if measure == "temperature":
		sensor_id = sensor["args"][0]
		logger.debug("Reading "+'/sys/bus/w1/devices/'+sensor_id+'/w1_slave')
	        with open('/sys/bus/w1/devices/'+sensor_id+'/w1_slave', 'r') as content_file:
			return content_file.read()
	else: logger.error(measure+" not supported by "+__name__)

# parse the measure
def parse(sensor,measure,data):
	if measure == "temperature":
		start = data.find("t=")
	        return float(data[start+2:start+7])/1000
	else: logger.error(measure+" not supported by "+__name__)

# return the cache schema
def schema(measure):
	return measure
