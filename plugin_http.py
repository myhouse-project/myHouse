#!/usr/bin/python

import sys
import os
import base64

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# return an image not available picture
def get_image_unavailable():
	with open(conf["constants"]["image_unavailable"],'r') as file:
        	data = base64.b64encode(file.read())
	file.close()
	return data

# poll the sensor
def poll(sensor):
	# set the parameters
	username = sensor['plugin']['username'] if 'username' in sensor['plugin'] else None
	password = sensor['plugin']['password'] if 'password' in sensor['plugin'] else None
	binary =  sensor['plugin']['image'] if 'image' in sensor['plugin'] else False
	# visit the page
	try:
		data = utils.web_get(sensor['plugin']['url'],username,password,binary=binary)
        except Exception,e:
                log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to visit "+sensor['plugin']['url']+": "+utils.get_exception(e))
		return ""
	# return empty if the data is not binary
	if binary:
		if "<html" in data.lower() or data == "": return ""
	# return the data, if binary return the base64 encoding
	if binary: return base64.b64encode(data)
	else: return data

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = data
	# if expecting an image and no data or an error is returned, return a placeholder
	if sensor['plugin']['image'] and measure["value"] == "": measure["value"] = get_image_unavailable()
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	return sensor['plugin']['url']

