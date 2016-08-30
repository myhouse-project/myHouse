#!/usr/bin/python

import sys
import os
import base64

import utils
import logger
log = logger.get_logger(__name__)

# poll the sensor
def poll(sensor):
	# visit the url, if an image is requested, return the base64 encoded data
	username =  sensor['plugin']['username'] if 'username' in sensor['plugin'] else None
	password =  sensor['plugin']['password'] if 'password' in sensor['plugin'] else None
	binary =   sensor['plugin']['binary'] if 'binary' in sensor['plugin'] else False
	return base64.b64encode(utils.web_get(sensor['plugin']['url'],username,password,binary=binary))

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = data
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	return sensor['sensor_id']

