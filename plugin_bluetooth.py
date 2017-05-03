#!/usr/bin/python
import re

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

if "bluetooth" in conf["plugins"]:
	plugin_conf = conf["plugins"]["bluetooth"]
	hci = plugin_conf["adapter"]
scan_timeout = 10
notification_timeout = 10

# poll the sensor
def poll(sensor):
	# return the raw value 
	value = ""
	if sensor["plugin"]["handle_type"] == "value": value = get_value(sensor["plugin"]["mac"],sensor["plugin"]["handle"])
	elif sensor["plugin"]["handle_type"] == "notification": value = get_notification(sensor["plugin"]["mac"],sensor["plugin"]["handle"])
	else: log.error("Invalid handle type: "+sensor["plugin"]["handle_type"])
	log.debug("polled: "+str(value))
	return value

# parse the data
def parse(sensor,data):
	if data is "": return None
	# get what data format this sensor would expect
	formatter = conf["constants"]["formats"][sensor["format"]]["formatter"]
	# format the hex data into the expected format
	if formatter == "int" or formatter == "float_1" or formatter == "float_2": data = utils.hex2int(data)
	elif formatter == "string": data = utils.hex2string(data)
	else: log.error("Invalid formatter: "+str(formatter))
	# apply any transformation if needed
	if "transform" in sensor["plugin"]:
		if sensor["plugin"]["transform"] == "/10": data = float(data)/10
		if sensor["plugin"]["transform"] == "/100": data = float(data)/100
	return data

# return the cache schema
def cache_schema(sensor):
	return sensor["plugin"]["mac"]+"_"+sensor["plugin"]["handle"]

# read a value from the device handle and return its hex
def get_value(device,handle):
	# use char read
	output = utils.run_command("gatttool -i "+hci+" -b "+device+" -t random --char-read -a "+handle)
	# clean up the output
	return output.replace("Characteristic value/descriptor: ","")

# read a value from the device notification handle and return its hex
def get_notification(device,handle):
	# enable notification on the provided handle
	output = utils.run_command(["gatttool","-i",hci,"-b",device,"-t","random","--char-write-req","-a",handle,"-n","0100","--listen"],shell=False,timeout=notification_timeout)
	# disable notifications
	utils.run_command("gatttool -i "+hci+" -b "+device+" -t random --char-write-req -a "+handle+" -n 0000")
	# find all the values
	values = re.findall("value: (.+)\n",output)
	# return the first match
	if len(values) > 0: return values[0]
	return ""

# discover BLE devices
def discover(): 
	print "Scanning for BLE devices..."
	scan = utils.run_command("hcitool -i "+hci+" lescan",timeout=scan_timeout)
	# search for MAC addresses
	devices = set(re.findall("(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)",scan))
	print "Found "+str(len(devices))+" device(s):"
	# for each device
	for device in devices:
		print "\t- Device "+device+":"
		# for value handles read the characteristics
		characteristics = utils.run_command("gatttool -i "+hci+" -b "+device+" -t random --characteristics")
		# filter by char properties (02 and 12 is READ)
		value_handles = re.findall("char properties = 0x(12|02), char value handle = (.+), uuid =",characteristics)
		for value_handle in value_handles:
			# for each handle
			handle = value_handle[1]
			# read the value
			value = get_value(device,handle)
			print "\t\t - Value handle "+handle+", value: "+str(value)+", int="+str(utils.hex2int(value))+", string="+str(utils.hex2string(value))
		# for notification handles, find all the handles with 2902 UUID
		notifications = utils.run_command("gatttool -i "+hci+" -b "+device+" -t random --char-read -u 2902")
		notification_handles = re.findall("handle: (\S+) ",notifications)
		for notification_handle in notification_handles:
			# for each handle
			handle = notification_handle
			# get the value by enabling notifications
			value = get_notification(device,handle)
			print "\t\t - Notification handle "+handle+", value: "+str(value)+", int="+str(utils.hex2int(value))+", string="+str(utils.hex2string(value))	

	
# allow running it both as a module and when called directly
if __name__ == '__main__':
	# run the discover service
        discover()
