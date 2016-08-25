#!/usr/bin/python
##
# Sensor for DS18B20
# args: [<latitude>,<longitude>]
# measures: temperature

import subprocess

import utils
import logger
log = logger.get_logger(__name__)

# run a command and return the output
def execute(command):
	log.debug("Executing "+command)
	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        for line in process.stdout.readlines():
        	output = output+line
	return output.rstrip()
	

# poll the sensor
def poll(sensor):
	return execute(sensor["request"]+" "+sensor["args"][0])

# parse the data
def parse(sensor,data):
	measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
	parsed = execute("echo '"+data+"' |"+sensor["args"][1])
	measure["value"] = float(parsed)
        # append the measure and return it
        measures.append(measure)
        return measures

# return the cache schema
def cache_schema(request):
	return request

