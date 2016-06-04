## ds18b20 sensor module
# INPUT: sensor_id
# OUTPUT: temperature
import sys
import json
import os

# configuration settings
debug=0
module=1

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)
if (config["debug"]): debug = 1

# output mapping
mapping = ['temperature']

# read from the sensor and print the output
def main(args):
	# check command line arguments
	if len(args) == 0: 
		print "ERROR_ARGV"
		sys.exit(1)
	sensor_id = args[0]
	# opent the device
	with open('/sys/bus/w1/devices/'+sensor_id+'/w1_slave', 'r') as content_file:
		content = content_file.read()
		if debug: print content
		# retrieve the temperature
		start = content.find("t=")
		temp = float(content[start+2:start+7])/1000
		# print it
		output = []
	        entry = {}
		entry["temperature"] = temp
		output.append(entry)
	        output_json = json.dumps(output)
		if module: return output_json
		else: print output_json

# allow running it both as a module and when called directly
if __name__ == '__main__':
	module=0
	del sys.argv[0]
	main(sys.argv)
