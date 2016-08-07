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
	log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] polling sensor")
        try: 
		data = plugin.poll(sensor)
	except Exception,e: 
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to poll: "+utils.get_exception(e))
        # store it in the cache
        db.set(sensor["db_schema_cache"],data,utils.now())

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor):
	# parse the data out of the cache
	data = db.range(sensor["db_schema_cache"],withscores=False)[0]
	measures = None
        try:
		# parse the cached data
		measures = plugin.parse(sensor,data)
		# format each values
		for i in range(len(measures)): measures[i]["value"] = utils.normalize(measures[i]["value"])
	except Exception,e:
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to parse "+str(data)+": "+utils.get_exception(e))
	log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] parsed: "+str(measures))
	return measures

# save the data of a sensor into the database
def save(plugin,sensor):
	cache_timestamp = 0
	# get the data out of the cache
	if db.exists(sensor["db_schema_cache"]):
		data = db.range(sensor["db_schema_cache"],withscores=True)
		cache_timestamp = data[0][0]
	# if too old, refresh it
	if utils.now() - cache_timestamp > conf['modules'][sensor["module"]]['cache_valid_for_seconds']:
		poll(plugin,sensor)
	# get the parsed data
	measures = parse(plugin,sensor)
	# for each returned measure
	for measure in measures:
	        # set the timestamp to now if not already set
	        if "timestamp" not in measure:  measure["timestamp"] = utils.now()
		# delete previous values if no history has to be kept
		if not constants.sensor_types[sensor["type"]]["avg"]: db.delete(sensor['db_schema_measure'])
		# store the value into the database
		db.set(sensor["db_schema_measure"],measure["value"],measure["timestamp"])

# calculate min, max and avg value
def summarize(sensor,read_from,write_to,start,end):
	# retrieve from the database the data based on the given timeframe
	data = db.rangebyscore(sensor["db_schema"]+read_from,start,end,withscores=False)
	# calculate min,max,avg
	if constants.sensor_types[sensor["type"]]["avg"]:
		avg = utils.avg(data)
                log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] summarized "+read_from+"->"+write_to+":avg: "+str(avg))
       		db.set(sensor["db_schema"]+write_to+":avg",avg,end)
	if constants.sensor_types[sensor["type"]]["min_max"]:
		min = utils.min(data)
                log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] summarized "+read_from+"->"+write_to+":min: "+str(min))
                db.set(sensor["db_schema"]+write_to+":min",min,end)
		max = utils.max(data)
                log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] summarized "+read_from+"->"+write_to+":max: "+str(max))
                db.set(sensor["db_schema"]+write_to+":max",max,end)

# read or save the measure of a given sensor
def run(module,group_id,sensor_id,task):
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
        sensor['db_schema'] = constants.db_schema["root"]+":"+sensor["module"]+":sensors:"+sensor["group_id"]+":"+sensor["sensor_id"]
	sensor['db_schema_measure'] = sensor["db_schema"]
        sensor['db_schema_cache'] = constants.db_schema["root"]+":"+sensor["module"]+":__cache__:"+sensor["group_id"]+":"+sensor["plugin"]+"_"+plugin.cache_schema(sensor["type"])
	# execute the task
	log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] requested "+task)
	if task == "poll":
		# delete from the cache the previous value 
		db.delete(sensor['db_schema_cache'])
		# read the measure (will be stored into the cache)
		poll(plugin,sensor)
	elif task == "parse":
		# just parse the output
		parse(plugin,sensor)
	elif task == "save":
		# save the parsed output into the database
		save(plugin,sensor)
	elif task == "summarize_hour": 
		# every hour calculate and save min,max,avg of the previous hour
		summarize(sensor,'',":hour",utils.last_hour_start(),utils.now())
        elif task == "summarize_day":
		# every day calculate and save min,max,avg of the previous day (using hourly averages)
                summarize(sensor,":hour:avg",":day",utils.last_day_start(),utils.now())
	else: log.error("Unknown task "+task)

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
	# module,sensor_id,measure,action
        run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
