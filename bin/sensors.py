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

# read data out of a sensor and store the output in the cache
def read(plugin,sensor,measure):
	# read the data
        data = plugin.read(sensor,measure)
        # store it in the cache
        db.set(db.schema["sensors_cache"]+":"+sensor["id"]+":"+plugin.schema(measure),data,utils.now())

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor,measure):
	# parse the data out of the cache
        data = db.range(db.schema["sensors_cache"]+":"+sensor["id"]+":"+plugin.schema(measure),withscores=False)[0]
        return plugin.parse(sensor,measure,data)

# read or save the measure of a given sensor
def main(module,sensor_id,measure,task):
	sensor = config['modules'][module]['sensors'][sensor_id]
	sensor['id'] = sensor_id
        # determine the plugin to use 
	if sensor["plugin"] == "ds18b20": plugin = sensor_ds18b20
        elif sensor["plugin"] == "wunderground": plugin = sensor_wunderground
	else: logger.error("Plugin "+sensor["plugin"]+" not supported")

	logger.info("["+module+"] requested "+sensor["name"]+" "+measure+" "+task)
	# execute the task
	if task == "read": 
		read(plugin,sensor,measure)
	if task == "parse":
		logger.info("Parsed: "+str(utils.normalize(parse(plugin,sensor,measure))))
	if task == "save":
		timestamp = 0
		# get the data out of the cache
		if db.exists(db.schema["sensors_cache"]+":"+sensor["id"]+":"+plugin.schema(measure)):
			data = db.range(db.schema["sensors_cache"]+":"+sensor["id"]+":"+plugin.schema(measure),withscores=True)
			timestamp = data[0][0]
		# if too old, refresh it
		if utils.now() - timestamp > config['modules'][module]['ttl']:
			read(plugin,sensor,measure)
		# save the parsed data
		value = utils.normalize(parse(plugin,sensor,measure))
		logger.info("Read "+str(sensor["id"])+" "+measure+" ("+sensor["plugin"]+"): "+str(value))
		db.set(db.schema["sensors"]+":"+sensor["id"]+":"+measure,value,utils.now())
		

# allow running it both as a module and when called directly
if __name__ == '__main__':
	# module,sensor_id,measure,action
        main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
