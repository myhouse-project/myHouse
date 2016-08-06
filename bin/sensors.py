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

import sensor_ds18b20
import sensor_wunderground
import sensor_weatherchannel

# read data out of a sensor and store the output in the cache
def poll(plugin,sensor):
	# poll the data
	data = None
	log.info("["+sensor["module"]+"] polling "+sensor["id"]+" "+sensor["measure"]+"...")
        try: 
		data = plugin.poll(sensor)
	except Exception,e: 
		log.warning("Unable to poll sensor "+sensor["id"]+" "+sensor["measure"]+": "+utils.get_exception(e))
        # store it in the cache
        db.set(sensor["db_schema_cache"],data,utils.now())

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor):
	# parse the data out of the cache
	data = db.range(sensor["db_schema_cache"],withscores=False)[0]
	parsed = None
        try:
		parsed = utils.normalize(plugin.parse(sensor,data))
	except Exception,e:
		log.warning("Unable to parse "+str(data)+" for sensor "+sensor["id"]+" "+sensor["measure"]+": "+utils.get_exception(e))
	log.info("["+sensor["module"]+"] parsing "+sensor["id"]+" "+sensor["measure"]+": "+str(parsed))
	return parsed

# calculate min, max and avg value
def summarize(sensor,read_from,write_to,start,end):
	# retrieve from the database the data based on the given timeframe
	data = db.rangebyscore(sensor["db_schema"]+read_from,start,end,withscores=False)
	# calculate min,max,avg
	if constants.sensor_measures[sensor["measure"]]["avg"]:
		avg = utils.avg(data)
                log.info("["+sensor["module"]+"] summarizing "+sensor["id"]+" "+sensor["measure"]+" "+read_from+"->"+write_to+":avg: "+str(avg))
       		db.set(sensor["db_schema"]+write_to+":avg",avg,end)
	if constants.sensor_measures[sensor["measure"]]["min_max"]:
		min = utils.min(data)
                log.info("["+sensor["module"]+"] summarizing "+sensor["id"]+" "+sensor["measure"]+" "+read_from+"->"+write_to+":min: "+str(min))
                db.set(sensor["db_schema"]+write_to+":min",min,end)
		max = utils.max(data)
                log.info("["+sensor["module"]+"] summarizing "+sensor["id"]+" "+sensor["measure"]+" "+read_from+"->"+write_to+":max: "+str(max))
                db.set(sensor["db_schema"]+write_to+":max",max,end)

# read or save the measure of a given sensor
def run(module,sensor_id,measure,task):
	# ensure the sensor and measure exist
	if module not in conf['modules']: log.error("Module "+module+" not configured")
	if sensor_id not in conf['modules'][module]['sensors']: log.error(module+" sensor "+sensor_id+" not configured")
	if measure not in conf['modules'][module]['sensors'][sensor_id]['measures']: log.error(module+" measure "+measure+" of "+sensor_id+" not configured")
	# add to the sensor object all the required info
	sensor = conf['modules'][module]['sensors'][sensor_id]['measures'][measure]
	sensor['module'] = module
	sensor['id'] = sensor_id
	sensor['measure'] = measure
        # determine the plugin to use 
	if sensor["plugin"] == "ds18b20": plugin = sensor_ds18b20
        elif sensor["plugin"] == "wunderground": plugin = sensor_wunderground
	elif sensor["plugin"] == "weatherchannel": plugin = sensor_weatherchannel
	else: log.error("Plugin "+sensor["plugin"]+" not supported")
	# define the database schema
        sensor['db_schema'] = constants.db_schema["root"]+":"+sensor["module"]+":sensors:"+sensor["id"]+":"+sensor["measure"]
	sensor['db_schema_measure'] = sensor["db_schema"]
        sensor['db_schema_cache'] = constants.db_schema["root"]+":"+sensor["module"]+":__cache__:"+sensor["id"]+":"+sensor["plugin"]+"_"+plugin.cache_schema(sensor["measure"])
	# execute the task
	log.info("["+sensor["module"]+"] requested "+sensor["id"]+" "+sensor["measure"]+" "+task)
	if task == "poll":
		# delete from the cache the previous value 
		db.delete(sensor['db_schema_cache'])
		# read the measure (will be stored into the cache)
		poll(plugin,sensor)
	elif task == "parse":
		# just parse the output
		parse(plugin,sensor)
	elif task == "read":
		timestamp = 0
		# get the data out of the cache
		if db.exists(sensor["db_schema_cache"]):
			data = db.range(sensor["db_schema_cache"],withscores=True)
			timestamp = data[0][0]
		# if too old, refresh it
		if utils.now() - timestamp > conf['modules'][module]['cache_valid_for_seconds']:
			poll(plugin,sensor)
		# get the parsed data
		value = parse(plugin,sensor)
		# delete previous values if no history has to be kept
		if not constants.sensor_measures[sensor["measure"]]["avg"]: db.delete(sensor['db_schema_measure'])
		# store the value into the database
		db.set(sensor["db_schema_measure"],value,utils.now())
	elif task == "summarize_hour": 
		# every hour calculate and save min,max,avg of the previous hour
		summarize(sensor,'',":hour",utils.last_hour_start(),utils.now())
        elif task == "summarize_day":
		# every day calculate and save min,max,avg of the previous day (using hourly averages)
                summarize(sensor,":hour:avg",":day",utils.last_day_start(),utils.now())
	else: log.error("Unknown task "+task)

# allow running it both as a module and when called directly
if __name__ == '__main__':
	# module,sensor_id,measure,action
        run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
