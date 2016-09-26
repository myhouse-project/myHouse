#!/usr/bin/python
import datetime
import json
import sys
import time
import os
import socket
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors

# registered_sensors[<node_id>][<request>] = sensor
# e.g. registered_sensors["HA"]["TEMP"]
registered_sensors = {}
plugin_conf = conf['plugins']['sensors']['messagebridge']

# register a new sensor against this plugin
def register_sensor(sensor):
	if sensor['plugin']['name'] != 'messagebridge': return
	if sensor['plugin']['node_id'] not in registered_sensors: registered_sensors[sensor['plugin']['node_id']] = {}
	registered_sensor = registered_sensors[sensor['plugin']['node_id']]
	if sensor['plugin']['request'] not in registered_sensor: registered_sensor[sensor['plugin']['request']] = {}
	# add the sensor to the registered sensors
	registered_sensor[sensor['plugin']['request']] = sensor
	log.debug("["+__name__+"]["+sensor['plugin']['node_id']+"]["+sensor['plugin']['request']+"] registered sensor "+sensor['module_id']+":"+sensor['sensor_id']+":"+sensor['sensor_id'])

# run the push service
def run():
	log.debug("["+__name__+"] listening for UDP datagrams on port "+str(plugin_conf['port']))
	# bind to the network
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.bind(("",plugin_conf['port']))
	while True:
		# new data arrives	
		data, addr = sock.recvfrom(1024)
		log.debug("["+__name__+"] received "+data)
		data = json.loads(data)
		if data["type"] != "WirelessMessage": continue
		# check if it belongs to a registered sensor
		if data["id"] not in registered_sensors: continue
		registered_sensor = registered_sensors[data["id"]]
		# for each value
		for value in data["data"]:
			measures = []
			# for each registered request for this node_id
			for request,sensor in registered_sensor.iteritems():
				# skip if not a registered measure
				if not value.startswith(request): continue
				measure = {}
				# generate the timestamp
		                date = datetime.datetime.strptime(data["timestamp"],"%d %b %Y %H:%M:%S +0000")
		                measure["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
				measure["key"] = sensor["sensor_id"]
				# strip out the measure from the value
		                measure["value"] = float(value.replace(request,""))
		                measures.append(measure)
				sensors.store(sensor,measures)

