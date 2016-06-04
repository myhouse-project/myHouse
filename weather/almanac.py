## almanac
# INPUT: location
# OUTPUT: json forecast

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

# retrieve the almanac and print the output
def main(args):
	# check command line arguments
        if len(args) == 0:
                print "ERROR_ARGV"
                sys.exit(1)
	query = args[0]
	# read forecast using wunderground api
	try:
		output_json = requests.get('http://api.wunderground.com/api/'+config["weather_wunderground_api_key"]+'/almanac/q/'+query+'.json').text
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)
	if debug : print output_json
	if module: return output_json
	else: print output_json

# allow running it both as a module and when called directly
if __name__ == '__main__':
        module=0
        del sys.argv[0]
	main(sys.argv)
