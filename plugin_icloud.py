#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sys
import os
import base64
from pyicloud import PyiCloudService
from pyicloud.cmdline import main
from motionless import LatLonMarker,DecoratedMap

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
	# authenticate against icloud
	try:
		icloud = PyiCloudService(sensor["plugin"]["username"])
	except Exception,e:
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to access icloud: "+utils.get_exception(e))
		return ""
	# retrieve the devices
	devices = icloud.devices
	# for each device
	map = DecoratedMap(maptype=conf["constants"]["map_type"],size_x=conf["constants"]["map_size_x"],size_y=conf["constants"]["map_size_y"])
	for i, device in enumerate(devices):
		device = devices[i]
		if "devices" in sensor["plugin"] and device["name"] not in sensor["plugin"]["devices"]: continue
		# retrieve the location
		location = device.location()
		if location is None: continue
		# add the marker to the map
		map.add_marker(LatLonMarker(location["latitude"],location["longitude"], label=device["name"][0]))
	# download the map
	url = map.generate_url()
	try:
		data = utils.web_get(url,binary=True)
        except Exception,e:
                log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to visit "+url+": "+utils.get_exception(e))
		return ""
	# return empty if the data is not binary
	if "<html" in data.lower() or data == "": return ""
	# return the data, if binary return the base64 encoding
	return base64.b64encode(data)

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = data
	# if expecting an image and no data or an error is returned, return a placeholder
	if measure["value"] == "": measure["value"] = get_image_unavailable()
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	return sensor['plugin']['username']


# main
if __name__ == '__main__':
	sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
	sys.exit(main())

