#!/usr/bin/python
import sys
import os

import utils
import db
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()

import sensor_ds18b20
import sensor_wunderground
import sensor_weatherchannel

# read data out of a sensor and store the output in the cache
def read(plugin,sensor,measure):
	# read the data
        data = plugin.read(sensor,measure)
        # store it in the cache
        db.set(sensor["db_schema_cache"],data,utils.now())

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor,measure):
	# parse the data out of the cache
        data = db.range(sensor["db_schema_cache"],withscores=False)[0]
        return plugin.parse(sensor,measure,data)

# calculate min, max and avg value
def summarize(sensor,read_from,write_to,start,end):
	data = db.rangebyscore(sensor["db_schema"]+":"+read_from,start,end,withscores=False)
	min = utils.min(data)
	max = utils.max(data)
	avg = utils.avg(data)
	if min is not None: db.set(sensor["db_schema"]+":"+write_to+":min",min,end)
	if max is not None: db.set(sensor["db_schema"]+":"+write_to+":max",min,end)
	if avg is not None: db.set(sensor["db_schema"]+":"+write_to+":avg",min,end)

# read or save the measure of a given sensor
def run(module,sensor_id,measure,task):
	sensor = config['modules'][module]['sensors'][sensor_id]['series'][measure]
	sensor['id'] = sensor_id
	sensor['measure'] = measure

        # determine the plugin to use 
	if sensor["plugin"] == "ds18b20": plugin = sensor_ds18b20
        elif sensor["plugin"] == "wunderground": plugin = sensor_wunderground
	elif sensor["plugin"] == "weatherchannel": plugin = sensor_weatherchannel
	else: logger.error("Plugin "+sensor["plugin"]+" not supported")
        sensor['db_schema'] = db.schema["root"]+":"+module+":sensors:"+sensor["id"]+":"+sensor["measure"]
	sensor['db_schema_measure'] = sensor["db_schema"]+":data"
        sensor['db_schema_cache'] = db.schema["root"]+":"+module+":cache:"+sensor["id"]+":"+sensor["plugin"]+"_"+plugin.schema(measure)

	logger.info("["+module+"] requested "+sensor["id"]+" "+measure+" "+task)
	# execute the task
	if task == "read": 
		db.delete(sensor['db_schema_cache'])
		read(plugin,sensor,measure)
	elif task == "parse":
		logger.info("Parsed: "+str(utils.normalize(parse(plugin,sensor,measure))))
	elif task == "save":
		timestamp = 0
		# get the data out of the cache
		if db.exists(sensor["db_schema_cache"]):
			data = db.range(sensor["db_schema_cache"],withscores=True)
			timestamp = data[0][0]
		# if too old, refresh it
		if utils.now() - timestamp > config['modules'][module]['ttl']:
			read(plugin,sensor,measure)
		# save the parsed data
		value = utils.normalize(parse(plugin,sensor,measure))
		# delete previous values if no history has to be kept
		if not sensor["keep_history"]: db.delete(sensor['db_schema_measure'])
		logger.info("Read "+str(sensor["id"])+" "+measure+" ("+sensor["plugin"]+"): "+str(value))
		db.set(sensor["db_schema_measure"],value,utils.now())
	elif task == "summarize_hour": 
		summarize(sensor,"measure","hour",utils.last_hour_start(),utils.now())
        elif task == "summarize_day":
                summarize(sensor,"hour:avg","day",utils.last_day_start(),utils.now())
	else: logger.error("Unknown task "+task)		

# allow running it both as a module and when called directly
if __name__ == '__main__':
	# module,sensor_id,measure,action
        run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
