#!/usr/bin/python
import datetime
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

# variables
registered_actuators = {}
queue = {}
plugin_conf = conf['plugins']['actuators']['messagebridge']

# register a new actuator against this plugin
def register_actuator(actuator):
	if actuator['plugin']['name'] != 'messagebridge': return
	registered_actuators[actuator['plugin']['node_id']] = actuator
	log.debug("["+__name__+"]["+actuator['plugin']['node_id']+"] registered actuator "+actuator['module_id']+":"+actuator['actuator_id'])

# send a message to a sensor
def send(node_id,data):
	# retrieve the actuator
	if node_id not in registered_actuators: return
	actuator = registered_actuators[node_id]
	if "sleep_min" not in actuator["plugin"]: 
		# send the message directly
		tx(node_id,data)
	else:
		# may be sleeping, queue it
		queue[node_id] = data
	

# transmit a message to a sensor
def tx(node_id,data):
        # create a socket
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# prepare the message
	message = {'type':"WirelessMessage",'network':"Serial"}
	message["id"] = node_id
	message["data"] = data
	json_message = json.dumps(message)
	# send the message
	log.debug("["+__name__+"] sending message: "+json_message)
	sock.sendto(json_message, ('<broadcast>',plugin_conf['port']))
	sock.close()

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
		# check if it belongs to a registered actuator
		if data["id"] not in registered_actuators: continue
		actuator = registered_actuators[data["id"]]
		# for each value
		for message in data["data"]:
			if message == "STARTED":
				# ACK a started message
				tx(data["id"],"ACK")
			elif message == "AWAKE":
				# if awaking, put it to sleep again, sending the queue if any first
				if "sleep_min" not in actuator["plugin"]: continue
				if data["id"] in queue: tx(data["id"],queue[data["id"]])
				del queue[data["id"]]
				tx(data["id"],"SLEEP0"+actuator["plugin"]["sleep_min"]+"M")

