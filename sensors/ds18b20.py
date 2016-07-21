#!/usr/bin/python
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../")
import core
logger = core.get_logger(__name__)
config = core.get_config()

def read(sensor,measure):
	if measure == "temperature":
		sensor_id = sensor["args"]
		logger.debug("Reading "+'/sys/bus/w1/devices/'+sensor_id+'/w1_slave')
	        with open('/sys/bus/w1/devices/'+sensor_id+'/w1_slave', 'r') as content_file:
			return content_file.read()
	else: logger.error(measure+" not supported by "+__name__)

def parse(sensor,measure,data):
	if measure == "temperature":
		start = data.find("t=")
	        return float(data[start+2:start+7])/1000
	else: logger.error(measure+" not supported by "+__name__)

def cache(measure):
	return measure
