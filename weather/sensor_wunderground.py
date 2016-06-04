## wunderground module
# INPUT: location
# OUTPUT: temperature

import requests
import json
import sys
import os

# configuration settings
debug = 0
module = 1

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
	query = args[0]
	# read current condition using wunderground api
	try:
		json_string = requests.get('http://api.wunderground.com/api/'+config["weather_wunderground_api_key"]+'/conditions/q/'+query+'.json').text
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)
	if debug : print json_string
	# parse json output
	parsed_json = json.loads(json_string)
	# print the current temperature
	output = []
	entry = {}
	entry["temperature"] = parsed_json['current_observation']['temp_c']
	entry["timestamp"] = parsed_json['current_observation']['observation_epoch']
	entry["condition"] = parsed_json['current_observation']['icon']
	output.append(entry)
	output_json = json.dumps(output)
	if module: return output_json
	else: print output_json

# allow running it both as a module and when called directly
if __name__ == '__main__':
        module=0
        del sys.argv[0]
	main(sys.argv)
