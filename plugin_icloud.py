#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sys
import os
import base64
from pyicloud import PyiCloudService
from pyicloud.cmdline import main
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

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
	locations = {}
        # for each device
        for i, device in enumerate(devices):
                device = devices[i]
                if "devices" in sensor["plugin"] and device["name"] not in sensor["plugin"]["devices"]: continue
                # retrieve the location
                location = device.location()
                if location is None: continue
		# keep the raw location
		locations[device["name"]] = location
	return json.dumps(locations)

# parse the data
def parse(sensor,data):
	data = json.loads(data)
	devices = []
	# for each device normalize the data for a map 
	for device_name in data:
		device = {}
		date = utils.timestamp2date(utils.timezone(int(data[device_name]["timeStamp"]/1000)))
		device["label"] = str(device_name)
		device["text"] = str("<p><b>"+device_name+":</b></p><p>"+date+" ("+data[device_name]["positionType"]+") </p>")
		device["latitude"] = data[device_name]["latitude"]
		device["longitude"] = data[device_name]["longitude"]
		device["accuracy"] = data[device_name]["horizontalAccuracy"]
		devices.append(device)
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = json.dumps(devices)
	measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	return sensor['plugin']['username']


# main
if __name__ == '__main__':
	sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
	sys.exit(main())

