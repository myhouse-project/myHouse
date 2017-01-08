#!/usr/bin/python
import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# poll the sensor
def poll(sensor):
	# ensure the device exists
	filename = "/sys/bus/w1/devices/"+sensor["plugin"]["device"]+"/w1_slave"
	if not utils.file_exists(filename):
		log.error(filename+" does not exist")
		return None
	# read the file
	log.debug("Reading temperature from "+filename)
	with open(filename, 'r') as file:
		data = file.read()
	file.close()
	return data

# parse the data
def parse(sensor,data):
	# find t=
	pos = data.find('t=')
	if pos != -1:
		temp_string = data[pos+2:]
		temp = float(temp_string) / 1000.0
		return temp

# return the cache schema
def cache_schema(sensor):
	return sensor["plugin"]["device"]
