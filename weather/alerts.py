## alerts
# INPUT: location
# OUTPUT: json forecast

import requests
import os
import json
import sys

# configuration settings
debug = 0
module = 1

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)
if (config["debug"]): debug = 1

# retrieve the alerts and print the output
def main(args):
	# check command line arguments
        if len(args) == 0:
                print "ERROR_ARGV"
                sys.exit(1)
	query = args[0].replace(',','/')
	# read forecast using the weather channel api
	try:
		output_json = requests.get('https://api.weather.com/v1/geocode/'+query+'/forecast/wwir.json?apiKey='+config["weather_weatherchannel_api_key"]+'&units=m&language=en').text
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
