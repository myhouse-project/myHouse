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

# nodes[<node_id>][<measure>] = sensor
# e.g. nodes["HA"]["TEMP"]
nodes = {}
queue = {}
plugin_conf = conf['plugins']['messagebridge']
default_measure = "__measure__"

# register a new sensor against this plugin
def register(sensor):
	if sensor['plugin']['plugin_name'] != 'messagebridge': return
	# create a data structure for each node_id
	node_id = sensor['plugin']['node_id']
	if node_id not in nodes: nodes[node_id] = {}
	# if no measures are provided, set it to the default_measure
	if "measure" not in sensor['plugin'] and "measures" not in sensor['plugin']: sensor['plugin']['measure'] = default_measure
	# merge the measures array with the single value measure
	measures = sensor['plugin']['measures'] if "measures" in sensor['plugin'] else [sensor['plugin']['measure']]
	# for each measure to register
	for measure in measures:
		# check if the measure has already been registered
		if measure in nodes[node_id]:
			log.warning("["+__name__+"]["+node_id+"]["+measure+"] already registered, skipping")
			continue
		# create a data structure for each measure of each node_id
		nodes[node_id][measure] = {}
		# add the sensor to the nodes list
		nodes[node_id][measure] = sensor
		log.debug("["+__name__+"]["+node_id+"]["+measure+"] registered sensor "+sensor['module_id']+":"+sensor['group_id']+":"+sensor['sensor_id'])
		# initialize the sensor
		if "cycle_sleep_min" in sensor["plugin"]: init(sensor)

# initialize a sensor when just started or when in an unknown status
def init(sensor):
	if not plugin_conf["enabled"]: return
	# turn all the output off
        tx(sensor,["OUTA0","OUTB0","OUTC0","OUTD0"],True)
	# put it to sleep
        sleep(sensor)

# send a message to the sensor
def send(sensor,data,force=False):
	if not plugin_conf["enabled"]: return
        # retrieve the sensor
        node_id = sensor["plugin"]["node_id"]
        if node_id not in nodes: return
        if "cycle_sleep_min" not in sensor["plugin"] or force:
                # send the message directly
                tx(sensor,data)
        else:
                # may be sleeping, queue it
                log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"]["+node_id+"] queuing message: "+data)
                if node_id not in queue: queue[node_id] = []
		queue[node_id] = [data]

# transmit a message to a sensor
def tx(sensor,data,service_message=False):
	if not plugin_conf["enabled"]: return
        node_id = sensor["plugin"]["node_id"]
        if not service_message: log.info("["+sensor["module_id"]+"]["+sensor["sensor_id"]+"]["+node_id+"] sending message: "+str(data))
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

# send a sensor to sleep
def sleep(sensor):
	sleep_min = sensor["plugin"]["cycle_sleep_min"]*60
	time.sleep(1)
        tx(sensor,"SLEEP"+str(sleep_min).zfill(3)+"S",False)


# run the plugin service
def run():
	if not plugin_conf["enabled"]: return
	log.debug("["+__name__+"] listening for UDP datagrams on port "+str(plugin_conf['port_listen']))
	# bind to the network
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.bind(("",plugin_conf['port_listen']))
	while True:
		try:
			# new data arrives	
			data, addr = sock.recvfrom(1024)
			log.debug("["+__name__+"] received "+data)
			data = json.loads(data)
			if data["type"] != "WirelessMessage": continue
			# check if it belongs to a registered sensor
			if data["id"] not in nodes: continue
			node = nodes[data["id"]]
			# for each measure
			for message in data["data"]:
	                        if message == "STARTED":
					if default_measure not in node: continue
					sensor = node[default_measure]
	                                log.info("["+sensor["module_id"]+"]["+sensor["sensor_id"]+"] has just started")
        	                        # ACK a started message
	                                tx(sensor,"ACK",True)
	                                # initialize
        	                        init(sensor)
	                        if message == "AWAKE":
					if default_measure not in node: continue
					sensor = node[default_measure]
	                                # send a message if there is something in the queue
	                                if data["id"] in queue and len(queue[data["id"]]) > 0:
	                                        tx(sensor,queue[data["id"]])
	                                        queue[data["id"]] = []
	                                # put it to sleep again
	                                sleep(sensor)
				# other messages can be a measure from the sensor
				measures = []
				# for each registered measure for this node_id
				for measure,sensor in node.iteritems():
					# skip if not a registered measure
					if not message.startswith(measure): continue
					measure_data = {}
					# generate the timestamp
			                date = datetime.datetime.strptime(data["timestamp"],"%d %b %Y %H:%M:%S +0000")
			                measure_data["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
					measure_data["key"] = sensor["sensor_id"]
					# strip out the measure from the value
			                measure_data["value"] = utils.normalize(message.replace(measure,""),conf["constants"]["formats"][sensor["format"]]["formatter"])
			                measures.append(measure_data)
					sensors.store(sensor,measures)
		except Exception,e:
			log.warning("unable to parse "+str(data)+": "+utils.get_exception(e))
