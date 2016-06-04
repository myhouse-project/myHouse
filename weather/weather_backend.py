## weather module
import time
import sys
import numpy
import json
import os
import redis

import sensor_ds18b20
import sensor_wunderground
import forecast
import almanac
import alerts
import email_notification

# configuration settings
debug = 0
write = 1

measures = {}
measures["temperature"] = {"type":"number","history":1}
measures["condition"] = {"type":"string","history":1}
measures["record"] = {"type":"number","history":0}

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)
if (config["debug"]):  debug = 1

# connect to the database
db = redis.StrictRedis(host=config["db_hostname"], port=config["db_port"], db=config["db_number"])

# read from the configured sensors
def measure():
	for sensor in config["weather_sensors"]:
		if debug: print "sensor: "+str(sensor)
		args = sensor["args"].split(':')
		# determine the module to use
		if sensor["type"] == "ds18b20": module = sensor_ds18b20
		if sensor["type"] == "wunderground": module = sensor_wunderground
		# read the data
		output = json.loads(module.main(args))
		if debug: print "result: "+str(output)
		# for each output
		for entry in output:
			# set the timestamp
			timestamp = int(time.time())
			if ("timestamp" in entry): timestamp = entry["timestamp"]
			for key in entry:
				# for each measure
				if (key == "timestamp"): continue
				db_key = config["weather_db_schema"]+":"+sensor["name"]+":"+key
				# keep history and store in measure
				db_key += ":measure"
				score = timestamp
				value = str(timestamp)+":"+str(entry[key])
				if debug: print "key: "+db_key+", score: "+str(score)+", value:"+value
				# add the value to the database
				if write: db.zadd(db_key,score,value)

# calculate min, max and avg value
def summarize(timeframe,timestamp_end): 
	timestamp_start = timestamp_end-config[timeframe]
	filter = "measure" if (timeframe == "hour") else "hour"
	# for each measure
	for measure in measures:
		if (not measures[measure]["history"]): continue
		keys = db.keys(config["weather_db_schema"]+":*:"+measure+":"+filter)
		# for each sensor
		for key in keys:
			root = key.replace(":"+filter,"")
			root += ":"+timeframe
			# read the data from timestamp start to end
			data = db.zrangebyscore(key,timestamp_start,timestamp_end)
			if (measures[measure]["type"] == "number"):
				value = [float(x.split(':')[1]) for x in data]
				# if a number calculate min, max, avg
				min_value,max_value,avg_value = min(value), max(value), numpy.mean(value)
				# store to the database (min)
				db_key = root+":min"
				score = timestamp_start
				value = str(timestamp_start)+":"+str(min_value)
				if write: db.zadd(db_key,score,value)
				if debug: print "key: "+db_key+", score: "+str(score)+", value: "+value
                                # store to the database (max)
                                db_key = root+":max"
                                score = timestamp_start
                                value = str(timestamp_start)+":"+str(max_value)
                                if write: db.zadd(db_key,score,value)
                                if debug: print "key: "+db_key+", score: "+str(score)+", value: "+value
                                # store to the database (range)
                                db_key = root+":range"
                                score = timestamp_start
                                value = str(timestamp_start)+":"+str(min_value)+":"+str(max_value)
                                if write: db.zadd(db_key,score,value)
                                if debug: print "key: "+db_key+", score: "+str(score)+", value: "+value
								# store to the database (avg)
                                db_key = root
                                score = timestamp_start
                                value = str(timestamp_start)+":"+str(avg_value)
                                if write: db.zadd(db_key,score,value)
                                if debug: print "key: "+db_key+", score: "+str(score)+", value: "+value
			else: 
				# if a string calculate the occurence seen the most
				value = [x.split(':')[1] for x in data]
				avg = max(set(value), key=value.count)
				db_key = root
                                score = timestamp_start
                                value = str(timestamp_start)+":"+avg
                                if write: db.zadd(db_key,score,value)
                                if debug: print "key: "+db_key+", score: "+str(score)+", value: "+value

# get the alerts
def get_alerts():
	output = alerts.main([config["weather_location_lat_lon"]])
        if debug: print output
        db.set("home:weather:alerts",output)

# get the almanac
def get_almanac():
	output = almanac.main([config["weather_location_lat_lon"]])
        if debug: print output
	# store min/max for record/normal
	output = json.loads(output)
	timestamp = int(time.time())
	if write: db.zadd(config["weather_db_schema"]+":almanac:record:max",timestamp,str(timestamp)+":"+output["almanac"]["temp_high"]["record"]["C"])
	if write: db.zadd(config["weather_db_schema"]+":almanac:record:min",timestamp,str(timestamp)+":"+output["almanac"]["temp_low"]["record"]["C"])
	if write: db.zadd(config["weather_db_schema"]+":almanac:normal:max",timestamp,str(timestamp)+":"+output["almanac"]["temp_high"]["normal"]["C"])
	if write: db.zadd(config["weather_db_schema"]+":almanac:normal:min",timestamp,str(timestamp)+":"+output["almanac"]["temp_low"]["normal"]["C"])

# get the forecast
def get_forecast():
	output = forecast.main([config["weather_location_lat_lon"]])
        if debug: print output
        db.set("home:weather:forecast",output)
			
	
# read command line arguments
if (len(sys.argv) == 2):
	if (sys.argv[1] == "measure"): 
		# Get measures from all the sensors
		measure()
        # retrieve the latest alerts
		get_alerts()
	if (sys.argv[1] == "hour"): 
		# summarize by hour
		summarize("hour",int(time.time()))
		# retrieve the latest forecast
		get_forecast()
	if (sys.argv[1] == "day"): 
		summarize("day",int(time.time()))
		# retrieve the almanac
		get_almanac()
		# send the email weather report
		email_notification.main()
