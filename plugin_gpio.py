#!/usr/bin/python
import datetime
import json
import time
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors

# variables
plugin_conf = conf['plugins']['gpio']
pins = {}
platform = utils.get_platform()
supported_platform = True if platform != "unknown" else False

# initialize the GPIO
if plugin_conf["enabled"]:
        # import GPIO module
        if platform == "raspberry_pi": import RPi.GPIO as GPIO
        elif platform == "orange_pi": import OPi.GPIO as GPIO
        # initialize GPIO
        if supported_platform:
		GPIO.setwarnings(False)
		mode = GPIO.BCM if plugin_conf["mode"] == "bcm" else GPIO.BOARD
		GPIO.setmode(mode)

# register a new sensor against this plugin
def register(sensor):
	if not plugin_conf["enabled"] or not supported_platform: return
	if sensor['plugin']['plugin_name'] != 'gpio': return
	if sensor['plugin']['setup'] != "input": return
	if "edge_detect" not in sensor['plugin']: return
	# register the sensor
	pin = sensor['plugin']['pin']
	if pin in pins:
		log.error("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] pin "+str(pin)+" already registered, skipping")
		return
	pins[pin] = sensor
	# set pull up / down resistor
	pull_up_down = None
	if "pull_up_down" in sensor["plugin"] and sensor["plugin"]["pull_up_down"] == "up": pull_up_down = GPIO.PUD_UP
	if "pull_up_down" in sensor["plugin"] and sensor["plugin"]["pull_up_down"] == "down": pull_up_down = GPIO.PUD_DOWN
	# setup the channel
	if platform == "orange_pi" and pull_up_down is not None:
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] Pull up/Pull down not supported on this platform, skipping")
		return
	if platform == "raspberry_pi": GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
	else: GPIO.setup(pin, GPIO.IN)
	# add callbacks
	edge_detect = sensor["plugin"]["edge_detect"]
	if edge_detect == "rising": GPIO.add_event_detect(pin, GPIO.RISING, callback=event_callback)
	elif edge_detect == "falling": GPIO.add_event_detect(pin, GPIO.FALLING, callback=event_callback)
	elif edge_detect == "both": GPIO.add_event_detect(pin, GPIO.BOTH, callback=event_callback)
	log.debug("["+__name__+"]["+str(pin)+"] registered sensor "+sensor['module_id']+":"+sensor['group_id']+":"+sensor['sensor_id'])

# handle the callbacks
def save(pin,value):
	sensor = pins[pin]
	log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] GPIO input on pin "+str(pin)+" is now "+str(value))
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = value
	measures.append(measure)
	sensors.store(sensor,measures)

# receive a callback
def event_callback(pin):
	if GPIO.input(pin): save(pin,1)
	else: save(pin,0)

# run the plugin service
def run():
	# cycle
	while True:
		time.sleep(10)

# poll the sensor
def poll(sensor):
	if sensor['plugin']['setup'] != "input": return
	pin = sensor["plugin"]["pin"]
	if GPIO.input(pin): return 1
	else: return 0

# parse the data
def parse(sensor,data):
	return int(data)

# return the cache schema
def cache_schema(sensor):
	return str(sensor["plugin"]["pin"])

# send a message to the sensor
def send(sensor,data):
	if not plugin_conf["enabled"] or not supported_platform: return
	data = int(data)
	if data != 0 and data != 1: 
		log.error("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] cannot send data: "+str(data))
		return
	log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] setting GPIO pin "+str(sensor["plugin"]["pin"])+" to "+str(data))
	GPIO.output(sensor["plugin"]["pin"],data)

