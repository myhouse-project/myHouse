#!/usr/bin/python
import time
import paho.mqtt.client as mqtt
import Queue
import socket
import serial

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors

# limitations
# - inclusion mode not supported
# - ota firmware update

# variables
# nodes[<node_id>][<child_id>][<type>] = sensor
# e.g. nodes["254"]["1"]["V_TEMP"] = sensor
nodes = {}
queue = {}
plugin_conf = conf["plugins"]["mysensors"]
gateway = None
gateway_type = None
# data types
commands = ["PRESENTATION","SET","REQ","INTERNAL","STREAM"]
acks = ["NOACK","ACK"]
types = []
types.append(["S_DOOR","S_MOTION","S_SMOKE","S_BINARY","S_DIMMER","S_COVER","S_TEMP","S_HUM","S_BARO","S_WIND","S_RAIN","S_UV","S_WEIGHT","S_POWER","S_HEATER","S_DISTANCE","S_LIGHT_LEVEL","S_ARDUINO_NODE","S_ARDUINO_REPEATER_NODE","S_LOCK","S_IR","S_WATER","S_AIR_QUALITY","S_CUSTOM","S_DUST","S_SCENE_CONTROLLER","S_RGB_LIGHT","S_RGBW_LIGHT","S_COLOR_SENSOR","S_HVAC","S_MULTIMETER","S_SPRINKLER","S_WATER_LEAK","S_SOUND","S_VIBRATION","S_MOISTURE","S_INFO","S_GAS","S_GPS","S_WATER_QUALITY"])
types.append(["V_TEMP","V_HUM","V_STATUS","V_PERCENTAGE","V_PRESSURE","V_FORECAST","V_RAIN","V_RAINRATE","V_WIND","V_GUST","V_DIRECTION","V_UV","V_WEIGHT","V_DISTANCE","V_IMPEDANCE","V_ARMED","V_TRIPPED","V_WATT","V_KWH","V_SCENE_ON","V_SCENE_OFF","V_HVAC_FLOW_STATE","V_HVAC_SPEED","V_LIGHT_LEVEL","V_VAR1","V_VAR2","V_VAR3","V_VAR4","V_VAR5","V_UP","V_DOWN","V_STOP","V_IR_SEND","V_IR_RECEIVE","V_FLOW","V_VOLUME","V_LOCK_STATUS","V_LEVEL","V_VOLTAGE","V_CURRENT","V_RGB","V_RGBW","V_ID","V_UNIT_PREFIX","V_HVAC_SETPOINT_COOL","V_HVAC_SETPOINT_HEAT","V_HVAC_FLOW_MODE","V_TEXT","V_CUSTOM","V_POSITION","V_IR_RECORD","V_PH","V_ORP","V_EC","V_VAR","V_VA","V_POWER_FACTOR"])
types.append(["V_TEMP","V_HUM","V_STATUS","V_PERCENTAGE","V_PRESSURE","V_FORECAST","V_RAIN","V_RAINRATE","V_WIND","V_GUST","V_DIRECTION","V_UV","V_WEIGHT","V_DISTANCE","V_IMPEDANCE","V_ARMED","V_TRIPPED","V_WATT","V_KWH","V_SCENE_ON","V_SCENE_OFF","V_HVAC_FLOW_STATE","V_HVAC_SPEED","V_LIGHT_LEVEL","V_VAR1","V_VAR2","V_VAR3","V_VAR4","V_VAR5","V_UP","V_DOWN","V_STOP","V_IR_SEND","V_IR_RECEIVE","V_FLOW","V_VOLUME","V_LOCK_STATUS","V_LEVEL","V_VOLTAGE","V_CURRENT","V_RGB","V_RGBW","V_ID","V_UNIT_PREFIX","V_HVAC_SETPOINT_COOL","V_HVAC_SETPOINT_HEAT","V_HVAC_FLOW_MODE","V_TEXT","V_CUSTOM","V_POSITION","V_IR_RECORD","V_PH","V_ORP","V_EC","V_VAR","V_VA","V_POWER_FACTOR"])
types.append(["I_BATTERY_LEVEL","I_TIME","I_VERSION","I_ID_REQUEST","I_ID_RESPONSE","I_INCLUSION_MODE","I_CONFIG","I_FIND_PARENT","I_FIND_PARENT_RESPONSE","I_LOG_MESSAGE","I_CHILDREN","I_SKETCH_NAME","I_SKETCH_VERSION","I_REBOOT","I_GATEWAY_READY","I_SIGNING_PRESENTATION","I_NONCE_REQUEST","I_NONCE_RESPONSE","I_HEARTBEAT_REQUEST","I_PRESENTATION","I_DISCOVER_REQUEST","I_DISCOVER_RESPONSE","I_HEARTBEAT_RESPONSE","I_LOCKED","I_PING","I_PONG","I_REGISTRATION_REQUEST","I_REGISTRATION_RESPONSE","I_DEBUG"])
types.append(["ST_FIRMWARE_CONFIG_REQUEST","ST_FIRMWARE_CONFIG_RESPONSE","ST_FIRMWARE_REQUEST","ST_FIRMWARE_RESPONSE","ST_SOUND","ST_IMAGE"])

# register a new sensor against this plugin
def register(sensor):
	if sensor["plugin"]["plugin_name"] != "mysensors": return
	node_id = sensor["plugin"]["node_id"]
	child_id = sensor["plugin"]["child_id"]
	command_string = sensor["plugin"]["command"]
	type_string = sensor["plugin"]["type"]
	# create a data structure for each node_id
	if node_id not in nodes: nodes[node_id] = {}
	# create a data structure for each child_id
	if child_id not in nodes[node_id]: nodes[node_id][child_id] = {}
	# create a data structure for each command
	if command_string not in nodes[node_id][child_id]: nodes[node_id][child_id][command_string] = {}
	# check if the type has already been registered
	if type_string in nodes[node_id][child_id][command_string]:
		log.warning("["+__name__+"]["+node_id+"]["+child_id+"]["+command_string+"]["+type_string+"] already registered, skipping")
		return
	# add the sensor to the nodes list
	nodes[node_id][child_id][command_string][type_string] = sensor
	log.debug("["+__name__+"]["+node_id+"]["+child_id+"]["+command_string+"]["+type_string+"] registered sensor "+sensor['module_id']+":"+sensor['group_id']+":"+sensor['sensor_id'])

# send a message to the sensor
def send(sensor,data,force=False):
	if not plugin_conf["enabled"]: return
	# retrieve the sensor
	node_id = sensor["plugin"]["node_id"]
	child_id = sensor["plugin"]["child_id"]
	command_string = sensor["plugin"]["command"]
	type_string = sensor["plugin"]["type"]
	if node_id not in nodes or child_id not in nodes[node_id]: return
	if "sleeping" not in sensor["plugin"] or force:
		# send the message directly
		tx(node_id,child_id,command_string,type_string,data)
	else:
		# may be sleeping, queue it
		log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"]["+node_id+"]["+child_id+"] queuing message: "+str(data))
		if node_id not in queue: queue[node_id] = Queue()
		queue[node_id].put([node_id,child_id,command_string,type_string,data])

# transmit a message to a sensor in the radio network
def tx(node_id,child_id,command_string,type_string,payload,ack=0,service_message=False):
	global gateway, gateway_type
	if gateway_type is None: return
	if not plugin_conf["enabled"]: return
	gateway_conf = plugin_conf["gateways"][gateway_type]
        # map the correspoding command and type
        command = commands.index(command_string)
        type = types[command].index(type_string)
        ack_string = acks[ack]
	if not service_message: log.info("["+str(node_id)+"]["+str(child_id)+"]["+command_string+"]["+type_string+"] sending message: "+str(payload))
	# send the message to the gateway
	if gateway_type == "serial":
                # prepare the message
                msg = str(node_id)+";"+str(child_id)+";"+str(command)+";"+str(ack)+";"+str(type)+";"+payload+"\n"
                # send the message through the serial port
                try:
                        gateway.write(msg)
                except Exception,e:
                        log.error("unable to send "+str(msg)+" to the serial gateway: "+utils.get_exception(e))
	elif gateway_type == "ethernet":
		# prepare the message
		msg = str(node_id)+";"+str(child_id)+";"+str(command)+";"+str(ack)+";"+str(type)+";"+payload+"\n"
		# send the message through the network socket
		try:
			gateway.sendall(msg)
                except Exception,e:
                        log.error("unable to send "+str(msg)+" to the ethernet gateway: "+utils.get_exception(e))
	elif gateway_type == "mqtt":
		# publish the payload to the mqtt broker
		topic = gateway_conf["publish_topic_prefix"]+"/"+str(node_id)+"/"+str(child_id)+"/"+str(command)+"/"+str(ack)+"/"+str(type)
		log.debug("publishing on topic "+topic+": "+str(payload))
		try: 
			gateway.publish(topic,str(payload))
		except Exception,e:
			log.error("unable to publish "+str(payload)+" on topic "+topic+": "+utils.get_exception(e))
	else: log.error("unknown gateway "+gateway_type)
		
# process an inbound message
def process_inbound(node_id,child_id,command,ack,type,payload):
	# ensure command and type are valid
	if command >= len(commands): 
		log.error("["+str(node_id)+"]["+str(child_id)+"] command not supported: "+str(command))
		return
	if type >= len(types[command]):
                log.error("["+str(node_id)+"]["+str(child_id)+"] type not supported: "+str(type))
                return
	# map the correspoding command and type string
	command_string = commands[command]
	type_string = types[command][type]
	ack_string = acks[ack]
	log.debug("["+str(node_id)+"]["+str(child_id)+"]["+command_string+"]["+type_string+"]["+ack_string+"] received: "+str(payload))
	# handle protocol messages
	if command_string == "PRESENTATION":
		# handle presentation messages
		log.info("["+str(node_id)+"]["+str(child_id)+"] presented as "+type_string)
	elif command_string == "SET":
		# handle set messages (messages from sensors handled below)
		log.info("["+str(node_id)+"]["+str(child_id)+"]["+command_string+"]["+type_string+"]: "+payload)
	elif command_string == "REQ":
		# handle req messages
		log.info("["+str(node_id)+"]["+str(child_id)+"]["+command_string+"]["+type_string+"]: "+payload)
	elif command_string == "INTERNAL":
		# handle internal messages
		if type_string == "I_TIME":
			# return the time as requested by the sensor
			log.info("["+str(node_id)+"] requesting timestamp")
			tx(node_id,child_id,command_string,type_string,int(time.time()))
                elif type_string == "I_SKETCH_NAME":
			# log the sketch name
                        log.info("["+str(node_id)+"] reported sketch name: "+str(payload))
		elif type_string == "I_SKETCH_VERSION":
			# log the sketch version
			log.info("["+str(node_id)+"] reported sketch version: "+str(payload))
		elif type_string == "I_ID_REQUEST":
			# return the next available id
			log.info("["+str(node_id)+"] requesting node_id")
			id = 1
			tx(node_id,child_id,command_string,"I_ID_RESPONSE",id)
		elif type_string == "I_CONFIG":
			# return the controller's configuration
			log.info("["+str(node_id)+"] requesting configuration")
			metric = "I" if conf["general"]["units"]["imperial"] else "M"
			tx(node_id,child_id,command_string,type_string,metric)
		elif type_string == "I_BATTERY_LEVEL":
			# log the battery level
			log.info("["+str(node_id)+"] reporting battery level: "+str(payload)+"%")
		elif type_string == "I_LOG_MESSAGE":
			# log a custom message
			log.info("["+str(node_id)+"] logging: "+str(payload))
		elif type_string == "I_GATEWAY_READY":
			# report gateway report
			log.info("["+str(node_id)+"] reporting gateway ready")
		elif type_string == "I_HEARTBEAT_RESPONSE":
			# handle smart sleep
			log.info("["+str(node_id)+"] reporting heartbeat")
			if node_id in queue and not queue["node_id"].empty():
				# process the queue 
				while not queue["node_id"].empty():
					node_id,child_id,command_string,type_string,payload = queue["node_id"].get()
					# send the message
					tx(node_id,child_id,command_string,type_string,payload)
		else: log.info("["+str(node_id)+"] ignoring "+type_string)
	elif command_string == "STREAM":
		# handle stream messages
		return
	else: log.error("Invalid command "+command_string)
        # handle messages for registered sensors
        if node_id in nodes and child_id in nodes[node_id] and command_string in nodes[node_id][child_id] and type_string in nodes[node_id][child_id][command_string]:
                # message for a registered sensor
                sensor = nodes[node_id][child_id][command_string][type_string]
                # store the value for the sensor
                value = payload
                measures = []
                measure = {}
                measure["key"] = sensor["sensor_id"]
                measure["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
                measures.append(measure)
                sensors.store(sensor,measures)


# connect to a mqtt gateway
def gateway_run(gw_type):
        global gateway_type,gateway
        gateway_type = gw_type
        log.info("starting mysensors "+gateway_type+" gateway")
        gateway_conf = plugin_conf["gateways"][gateway_type]
	if gateway_type == "serial":
		try:
                    	# connect to the serial gateway
                        log.info("Connecting to serial gateway on "+gateway_conf["port"]+" with baud rate "+str(gateway_conf["baud"]))
                        gateway = serial.Serial(gateway_conf["port"],gateway_conf["baud"])
                except Exception,e:
                        log.warning("Unable to connect to the serial gateway: "+utils.get_exception(e))
                        return
                while True:
                        # read a line
                        try:
                                line = gateway.readline().rstrip()
                        except Exception,e:
                                log.warning("Unable to receive data from the serial gateway: "+utils.get_exception(e))
                                continue
                        # parse the line
                        try:
                                node_id,child_id,command,ack,type,payload = line.split(";")
                                # process the message
                                process_inbound(int(node_id),int(child_id),int(command),int(ack),int(type),payload)
                        except Exception,e:
                                log.warning("Invalid format: "+line)
                                continue
	elif gateway_type == "ethernet":
		try:
			# connect to the ethernet gateway
			log.info("Connecting to ethernet gateway on "+gateway_conf["hostname"]+":"+str(gateway_conf["port"]))
			gateway = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			gateway.connect((gateway_conf["hostname"],gateway_conf["port"]))
                except Exception,e:
                        log.warning("Unable to connect to the ehternet gateway: "+utils.get_exception(e))
                        return
		while True:
			# read a line
			try:
				line = ""
				while True:
					c = gateway.recv(1)
					if c == '\n' or c == '': break
					else: line += c
	                except Exception,e:
	                        log.warning("Unable to receive data from the ethernet gateway: "+utils.get_exception(e))
	                        continue
			# parse the line
			try:
				node_id,child_id,command,ack,type,payload = line.split(";")
	                        # process the message
        	                process_inbound(int(node_id),int(child_id),int(command),int(ack),int(type),payload)
			except Exception,e:
	                	log.warning("Invalid format: "+line)
	                        continue
        elif gateway_type == "mqtt":
                try:
                        # connect to the mqtt broker
			log.info("Connecting to mqtt gateway on "+gateway_conf["hostname"]+":"+str(gateway_conf["port"]))
                        gateway = mqtt.Client()
                        gateway.connect(gateway_conf["hostname"],gateway_conf["port"],60)
                except Exception,e:
                        log.warning("Unable to connect to the mqtt gateway: "+utils.get_exception(e))
                        return
                # define what to do on connect
                def mqtt_on_connect(client,userdata,flags,rc):
                        log.info("Connected to the mqtt gateway ("+str(rc)+")")
                        log.info("Subscribing to the mqtt topic "+gateway_conf["subscribe_topic_prefix"])
                        gateway.subscribe(gateway_conf["subscribe_topic_prefix"]+"/#")
		gateway.on_connect = mqtt_on_connect
                # define what to do when receiving a message
                def mqtt_on_message(client,userdata,msg):
                        try:
                                # split the topic
                                topic,node_id,child_id,command,ack,type = msg.topic.split("/")
                        except Exception,e:
                                log.warning("Invalid format: "+msg.topic)
                                return
                        # process the message
                        process_inbound(int(node_id),int(child_id),int(command),int(ack),int(type),msg.payload)
		gateway.on_message = mqtt_on_message
                # loop forever
                gateway.loop_forever()

# run the plugin service
def run():
	if not plugin_conf["enabled"]: return
	gateway_run(plugin_conf["gateway_type"])


run()
