## weather frontend module
import redis
import time
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

# webcams
def webcams():
	return json.dumps(config["weather_webcams"])

# weather query
def query(request,query):
    # retrieve the data from the database
	db = redis.StrictRedis(host=config["db_hostname"], port=config["db_port"], db=config["db_number"])
	data = db.get(config["weather_db_schema"]+":"+query)
	if debug: print "Returning "+str(data)
	# print the result
	return data

# weather data
def data(request,sensor_name,sensor_measure,timeframe):
	# define start and end timestamp
	start = int(time.time())-24*config["hour"]
	end = int(time.time())
	if (request.args.get('range')):
		start = -1
		end = -1
	if request.args.get('start'): start = int(request.args.get('start'))
	if request.args.get('end'): end = int(request.args.get('end'))
	# retrieve the data from the database
	db = redis.StrictRedis(host=config["db_hostname"], port=config["db_port"], db=config["db_number"])
	key = config["weather_db_schema"]+":"+sensor_name+":"+sensor_measure+":"+timeframe
	if debug: print "Requesting "+key+" "+str(start)+" "+str(end)
	if (request.args.get('range')): data = db.zrange(key,start,end)
	else: data = db.zrangebyscore(key,start,end)
	output = []
	for entry in data:
		value = entry.split(":");
		output_entry = [int(value[0])*1000]
		# for each value
		for i in range(1,len(value)):
			if (sensor_measure in ["temperature","record","normal"]): output_entry.append(float("{0:.1f}".format(float(value[i]))))
			else: output_entry.append(str(value[i]))
		output.append(output_entry)
	if debug: print "Returning "+str(output)
	# print the result
	return json.dumps(output)

# allow running it both as a module and when called directly
if __name__ == '__main__':
    module=0

