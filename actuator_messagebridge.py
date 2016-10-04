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
	# initialize the actuator and send it to sleep
	tx(actuator,["OUTA0","OUTB0","OUTC0","OUTD0"],True)
	sleep(actuator)

# send a message to the actuator
def send(actuator,data):
	# retrieve the actuator
	node_id = actuator["plugin"]["node_id"]
	if node_id not in registered_actuators: return
	actuator = registered_actuators[node_id]
	if "sleep_min" not in actuator["plugin"]: 
		# send the message directly
		tx(actuator,data)
	else:
		# may be sleeping, queue it
		log.info("["+actuator["module_id"]+"]["+actuator["actuator_id"]+"]["+node_id+"] queuing message: "+data)
		if node_id not in queue: queue[node_id] = []
		queue[node_id] = [data]
	
# transmit a message to an actuator
def tx(actuator,data,service_message=False):
	node_id = actuator["plugin"]["node_id"]
	if not service_message: log.info("["+actuator["module_id"]+"]["+actuator["actuator_id"]+"]["+node_id+"] sending message: "+str(data))
        # create a socket
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# prepare the message
	message = {'type':"WirelessMessage",'network':"Serial"}
	message["id"] = node_id
	message["data"] = data if isinstance(data,list) else [data]
	json_message = json.dumps(message)
	# send the message
	log.debug("["+__name__+"] sending message: "+json_message)
	sock.sendto(json_message, ('<broadcast>',plugin_conf['port_send']))
	sock.close()

# send an actuator to sleep
def sleep(actuator):
	time.sleep(2)
	tx(actuator,"SLEEP"+str(actuator["plugin"]["sleep_min"]).zfill(3)+"M",False)

# run the push service
def run():
	log.debug("["+__name__+"] listening for UDP datagrams on port "+str(plugin_conf['port_listen']))
	# bind to the network
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.bind(("",plugin_conf['port_listen']))
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
				log.info("["+actuator["module_id"]+"]["+actuator["actuator_id"]+"] has just started")
				# ACK a started message
				tx(actuator,"ACK",True)
				# put it to sleep
				sleep(actuator)
			elif message == "AWAKE":
				# send the message if there is something in the queue
				if data["id"] in queue and len(queue[data["id"]]) > 0: 
					tx(actuator,queue[data["id"]])
					queue[data["id"]] = []
				# put it to sleep again
				sleep(actuator)

