#!/usr/bin/python
import sys
import os

import utils
import db
import constants
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()

import sensor_ds18b20
import sensor_wunderground
import sensor_weatherchannel

# read data out of a sensor and store the output in the cache
def poll(plugin,sensor):
	# poll the data
	data = None
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] polling sensor")
        try: 
		data = plugin.poll(sensor)
	        # store it in the cache
	        db.set(sensor["db_cache"],data,utils.now())
	except Exception,e: 
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to poll: "+utils.get_exception(e))
	return data

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor):
	# parse the data out of the cache
	data = db.range(sensor["db_cache"],withscores=False)[0]
	measures = None
        try:
		# parse the cached data
		measures = plugin.parse(sensor,data)
		# format each values
		for i in range(len(measures)): measures[i]["value"] = utils.normalize(measures[i]["value"])
		log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] parsed: "+str(measures))
	except Exception,e:
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to parse "+str(data)+": "+utils.get_exception(e))
	return measures

# save the data of a sensor into the database
def save(plugin,sensor):
	cache_timestamp = 0
	# get the data out of the cache
	if db.exists(sensor["db_cache"]):
		data = db.range(sensor["db_cache"],withscores=True)
		cache_timestamp = data[0][0]
	# if too old, refresh it
	if utils.now() - cache_timestamp > conf['modules'][sensor["module"]]['cache_valid_for_seconds']:
		if poll(plugin,sensor) is None: return
	# get the parsed data
	measures = parse(plugin,sensor)
	if measures is None: return
	# for each returned measure
	for measure in measures:
	        # set the timestamp to now if not already set
	        if "timestamp" not in measure:  measure["timestamp"] = utils.now()
		# define the key to store the value
		key = sensor["db_group"]+":"+measure["key"]
		# delete previous values if no history has to be kept (e.g. single value)
		if not constants.sensor_types[sensor["type"]]["avg"]: db.delete(key)
		# check if the same value is already stored
		old = db.rangebyscore(key,measure["timestamp"],measure["timestamp"])
		if len(old) > 0:
			log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") ignoring "+measure["key"]+": "+str(measure["value"]))
			return
		# store the value into the database
		log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") saving "+measure["key"]+": "+utils.truncate(str(measure["value"])))
		db.set(key,measure["value"],measure["timestamp"])
		# re-calculate the avg/min/max of the hour/day
		if constants.sensor_types[sensor["type"]]["avg"]:
			summarize(sensor,'hour',utils.hour_start(measure["timestamp"]),utils.hour_end(measure["timestamp"]))
	                summarize(sensor,'day',utils.day_start(measure["timestamp"]),utils.day_end(measure["timestamp"]))

# calculate min, max and avg value
def summarize(sensor,timeframe,start,end):
	# prepare the database schema to use
	if timeframe == "hour": 
		key_to_read = sensor["db_sensor"]
		key_to_write = sensor["db_sensor"]+":hour"
	elif timeframe == "day":
                key_to_read = sensor["db_sensor"]+":hour:avg"
                key_to_write = sensor["db_sensor"]+":day"
	# retrieve from the database the data based on the given timeframe
	data = db.rangebyscore(key_to_read,start,end,withscores=False)
	timestamp = start
	min = avg = max = "-"
	if constants.sensor_types[sensor["type"]]["avg"]:
		# calculate avg
		avg = utils.avg(data)
		db.deletebyscore(key_to_write+":avg",start,end)
       		db.set(key_to_write+":avg",avg,timestamp)
	if constants.sensor_types[sensor["type"]]["min_max"]:
		# calculate min
		min = utils.min(data)
		db.deletebyscore(key_to_write+":min",start,end)
                db.set(key_to_write+":min",min,timestamp)
		# calculate max
		max = utils.max(data)
		db.deletebyscore(key_to_write+":max",start,end)
                db.set(key_to_write+":max",max,timestamp)
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(timestamp)+") updating summary of the "+timeframe+" (min,avg,max): ("+str(min)+","+str(avg)+","+str(max)+")")

# read or save the measure of a given sensor
def run(module,group_id,sensor_id,action):
	# ensure the group and sensor exist
	if module not in conf['modules']: log.error("["+module+"] not configured")
	if group_id not in conf['modules'][module]['sensor_groups']: log.error("["+module+"]["+group_id+"] not configured")
	if sensor_id not in conf['modules'][module]['sensor_groups'][group_id]['sensors']: log.error("["+module+"]["+group_id+"]["+sensor_id+"] not configured")
	# add to the sensor object all the required info
	sensor = conf['modules'][module]['sensor_groups'][group_id]['sensors'][sensor_id]
	sensor['module'] = module
	sensor['group_id'] = group_id
	sensor['sensor_id'] = sensor_id
        # determine the plugin to use 
	if sensor["plugin"] == "ds18b20": plugin = sensor_ds18b20
        elif sensor["plugin"] == "wunderground": plugin = sensor_wunderground
	elif sensor["plugin"] == "weatherchannel": plugin = sensor_weatherchannel
	else: log.error("Plugin "+sensor["plugin"]+" not supported")
	# define the database schema
        sensor['db_group'] = constants.db_schema["root"]+":"+sensor["module"]+":sensors:"+sensor["group_id"]
	sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
        sensor['db_cache'] = constants.db_schema["root"]+":"+sensor["module"]+":__cache__:"+sensor["group_id"]+":"+sensor["plugin"]+"_"+plugin.cache_schema(sensor["type"])
	# execute the action
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] requested "+action)
	if action == "poll":
		# delete from the cache the previous value 
		db.delete(sensor['db_cache'])
		# read the measure (will be stored into the cache)
		poll(plugin,sensor)
	elif action == "parse":
		# just parse the output
		parse(plugin,sensor)
	elif action == "save":
		# save the parsed output into the database
		save(plugin,sensor)
	elif action == "summarize_hour": 
		# every hour calculate and save min,max,avg of the previous hour
		summarize(sensor,'hour',utils.hour_start(utils.last_hour()),utils.hour_end(utils.last_hour()))
        elif action == "summarize_day":
		# every day calculate and save min,max,avg of the previous day (using hourly averages)
                summarize(sensor,'day',utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()))
	else: log.error("Unknown action "+action)

# schedule each sensor
def schedule_all():
        # for each module
        for module in constants.modules_with_sensors:
	        # for each group of sensors
                for group_id in conf["modules"][module]["sensor_groups"]:
			# for each sensor of the group
			for sensor_id in conf["modules"][module]["sensor_groups"][group_id]["sensors"]:
				sensor = conf["modules"][module]["sensor_groups"][group_id]["sensors"][sensor_id]
                                log.info("["+module+"]["+group_id+"]["+sensor_id+"] scheduling polling every "+str(sensor["refresh_interval_min"])+" minutes")
                                # schedule it
       	                        schedule.add_job(run,'cron',minute="*/"+str(sensor["refresh_interval_min"]),second=utils.randint(1,59),args=[module,group_id,sensor_id,'save'])
                                if constants.sensor_types[sensor["type"]]["avg"]:
       	                                # schedule a summarize job every hour and every day
               	                        log.info("["+module+"]["+group_id+"]["+sensor_id+"] scheduling summary every hour and day")
                       	                schedule.add_job(run,'cron',hour="*",args=[module,group_id,sensor_id,'summarize_hour'])
                               	        schedule.add_job(run,'cron',day="*",args=[module,group_id,sensor_id,'summarize_day'])


# allow running it both as a module and when called directly
if __name__ == '__main__':
	if (len(sys.argv) != 5): print "Usage: sensors.py <module> <group_id> <sensor_id> <action>"
	else: run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

