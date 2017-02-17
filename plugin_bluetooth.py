#!/usr/bin/python
import re

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# poll the sensor
def poll(sensor):
	command = sensor['plugin']['command_poll']
	# run the poll command
	command = "cd '"+conf["constants"]["base_dir"]+"'; "+command
	return utils.run_command(command,timeout=conf["plugins"]["command"]["timeout"])

# parse the data
def parse(sensor,data):
	data = str(data).replace("'","''")
	# no command parse, return the raw data
	if 'command_parse' not in sensor['plugin'] or sensor['plugin']['command_parse'] == "": return data
	command = "cd '"+conf["constants"]["base_dir"]+"'; echo '"+data+"' |"+sensor['plugin']['command_parse']
	return utils.run_command(command,timeout=conf["plugins"]["command"]["timeout"])

# return the cache schema
def cache_schema(sensor):
	return sensor['plugin']['command_poll']

# run a command
def send(sensor,data):
	# run the command in the script directory
	command = "cd '"+conf["constants"]["base_dir"]+"'; "+data
	utils.run_command(command,timeout=conf["plugins"]["command"]["timeout"])

# convert a hex string into an integer
def hex2int(hex):
	try:
		hex = "0x"+hex.replace(" ","")
		return int(hex, 16)
	except: return 0

# convert a hex string into a float and adjust based on precision
def hex2float(hex,precision = 0):
	int = float(hex2int(hex))
	if precision == 0: return int
	else: return int/(10*precision)

# convert a hex string into a ascii string
def hex2string(hex):
	try:
		string = hex.decode("hex")
		return string
	except: return ""

# read a value from the device handle
def get_value(device,handle):
	# use char read
	output = utils.run_command("gatttool -b "+device+" -t random --char-read -a "+handle)
	# clean up the output
	return output.replace("Characteristic value/descriptor: ","")

# read a value from the device notification handle
def get_notification(device,handle):
	# enable notification on the provided handle
	output = utils.run_command("gatttool -b "+device+" -t random --char-write-req -a "+handle+" -n 0100 --listen",timeout=10)
	# disable notifications
	utils.run_command("gatttool -b "+device+" -t random --char-write-req -a "+handle+" -n 0000")
	# find all the values
	values = re.findall("value: (.+)\n",output)
	# return the first match
	if len(values) > 0: return values[0]
	return ""

# discover BLE devices
def discover(): 
	print "Scanning for BLE devices..."
	scan = utils.run_command("hcitool lescan",timeout=5)
	# search for MAC addresses
	devices = set(re.findall("(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)",scan))
	print "Found "+str(len(devices))+" device(s):"
	# for each device
	for device in devices:
		print "\t- Device "+device+":"
		# for value handles read the characteristics
		characteristics = utils.run_command("gatttool -b "+device+" -t random --characteristics")
		# filter by char properties (02 and 12 is READ)
		value_handles = re.findall("char properties = 0x(12|02), char value handle = (.+), uuid =",characteristics)
		for value_handle in value_handles:
			# for each handle
			handle = value_handle[1]
			# read the value
			value = get_value(device,handle)
			print "\t\t - Read handle "+handle+", value: "+str(value)+", int="+str(hex2int(value))+", string="+str(hex2string(value))
		# for notification handles, find all the handles with 2902 UUID
		notifications = utils.run_command("gatttool -b "+device+" -t random --char-read -u 2902")
		notification_handles = re.findall("handle: (\S+) ",notifications)
		for notification_handle in notification_handles:
			# for each handle
			handle = notification_handle
			# get the value by enabling notifications
			value = get_notification(device,handle)
			print "\t\t - Notification handle "+handle+", value: "+str(value)+", int="+str(hex2int(value))+", string="+str(hex2string(value))	

	
# allow running it both as a module and when called directly
if __name__ == '__main__':
        discover()
