#!/usr/bin/python
import utils
import logger
import config
import Adafruit_DHT
log = logger.get_logger(__name__)
conf = config.get_config()

# poll the sensor
def poll(sensor):
	# set the device type
	if sensor["plugin"]["type"] == "dht11":
		dht_sensor = Adafruit_DHT.DHT11
	elif sensor["plugin"]["type"] == "dht22":
		dht_sensor = Adafruit_DHT.DHT22
	# read the measures
	humidity, temperature = Adafruit_DHT.read_retry(dht_sensor,sensor["plugin"]["pin"])
	if humidity is not None and temperature is not None and humidity <= 100:
		# if this is a valid measure, return both the measures
		return str(temperature)+"|"+str(humidity)

# parse the data
def parse(sensor,data):
	if "|" not in data: return
	split = data.split("|")
	if sensor["plugin"]["measure"] == "temperature": return split[0]
	if sensor["plugin"]["measure"] == "humidity": return split[1]

# return the cache schema
def cache_schema(sensor):
	return sensor["plugin"]["type"]+"_"+str(sensor["plugin"]["pin"])
