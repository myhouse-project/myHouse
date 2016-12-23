#!/usr/bin/python
import paho.mqtt.client as mqtt

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors

plugin_conf = conf['plugins']['mqtt']
topics = {}

# register a new sensor against this plugin
def register(sensor):
	if not plugin_conf["enabled"]: return
	if sensor['plugin']['plugin_name'] != 'mqtt': return
	if sensor['plugin']['mode'] != "subscribe": return
	# register the sensor
	topic = sensor['plugin']['topic']
	if topic in topics:
		log.error("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] topic "+str(topic)+" already registered, skipping")
		return
	topics[topic] = sensor
	log.debug("["+__name__+"]["+str(topic)+"] registered sensor "+sensor['module_id']+":"+sensor['group_id']+":"+sensor['sensor_id'])

# receive callback when conneting
def on_connect(client, userdata, flags, rc):
	log.debug("Connected to the MQTT gateway ("+str(rc)+")")
	# subscribe to the topics
	for topic in topics:
		log.debug("Subscribing to the MQTT topic "+topic)
		client.subscribe(topic)

# receive a callback when receiving a message
def on_message(client, userdata, msg):
	topic = msg.topic
	value = msg.payload
	if topic not in topics:
		log.warning("received a message from an invalid MQTT topic: "+topic)
		return
	sensor = topics[topic]
        log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] received "+str(value)+" for topic "+str(topic))
	# store the value
        measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
        measure["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
        measures.append(measure)
        sensors.store(sensor,measures)

# run the plugin service
def run():
	# connect to the gateway
	try: 
		log.info("Connecting to MQTT gateway on "+plugin_conf["hostname"]+":"+str(plugin_conf["port"]))
		client = mqtt.Client()
		client.connect(plugin_conf["hostname"],plugin_conf["port"],60)
	except Exception,e:
		log.warning("Unable to connect to the MQTT gateway: "+utils.get_exception(e))
		return
	# set callbacks
	client.on_connect = on_connect
	client.on_message = on_message
	# cycle
	client.loop_forever()

# send a message to the sensor
def send(sensor,data):
        if not plugin_conf["enabled"]: return
	# connect to the gateway
	client = mqtt.Client()
	client.connect(plugin_conf["hostname"],plugin_conf["hostname"],60)
	retain = False
	if "retain" in sensor["plugin"]: retain = sensor["plugin"]["retain"]
	# send the message
	log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] sending message "+str(data)+" to "+str(sensor["plugin"]["topic"]))
	client.publish(sensor["plugin"]["topic"],str(data),retain=retain)

