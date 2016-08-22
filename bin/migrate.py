#!/usr/bin/python

import logging

import utils
import db
import config
conf = config.get_config()
import sensors

######## START OF CONFIGURATION
# database number from which we are migrating
db_from = 0
# database number into which we are migrating
db_to = 1

# keys to migrate history (from key -> to key)
history = {
	'home:weather:outdoor:temperature:day:max': 'myHouse:weather:sensors:external_temperature:temperature:day:max',
	'home:weather:outdoor:temperature:day:min': 'myHouse:weather:sensors:external_temperature:temperature:day:min',
	'home:weather:outdoor:temperature:day': 'myHouse:weather:sensors:external_temperature:temperature:day:avg',

        'home:weather:indoor:temperature:day:max': 'myHouse:weather:sensors:internal_temperature:temperature_1:day:max',
        'home:weather:indoor:temperature:day:min': 'myHouse:weather:sensors:internal_temperature:temperature_1:day:min',
        'home:weather:indoor:temperature:day': 'myHouse:weather:sensors:internal_temperature:temperature_1:day:avg',

	'home:weather:almanac:record:min': 'myHouse:weather:sensors:external_temperature:record:day:min',
	'home:weather:almanac:record:max': 'myHouse:weather:sensors:external_temperature:record:day:max',

        'home:weather:almanac:normal:min': 'myHouse:weather:sensors:external_temperature:normal:day:min',
        'home:weather:almanac:normal:max': 'myHouse:weather:sensors:external_temperature:normal:day:max',

	'home:weather:outdoor:condition:day': 'myHouse:weather:sensors:external_temperature:condition:day:avg',
}

# keys to migrate recent data (from key -> to key)
recent = {
	'home:weather:outdoor:temperature:measure': 'myHouse:weather:sensors:external_temperature:temperature',
	'home:weather:indoor:temperature:measure': 'myHouse:weather:sensors:internal_temperature:temperature_1',
	'home:weather:outdoor:condition:measure': 'myHouse:weather:sensors:external_temperature:condition',
}

# enable history/recent migration
migrate_history = True
migrate_recent = True

#debug
debug = False
######## END OF CONFIGURATION

# change into a given database number
def change_db(database):
	db.db = None
	conf['db']['database'] = database

# for each history key to migrate
print "Migrating historical data..."
for key_from in history:
	if not migrate_history: break
	key_to = history[key_from]
	print "\tMigrating "+key_from+" -> "+key_to
	# retrieve all the data
	change_db(db_from)
	data = db.rangebyscore(key_from,"-inf",utils.now(),withscores=True)
	change_db(db_to)
	count = 0
	# for each entry
	for entry in data:
		timestamp = utils.day_start(utils.timezone(entry[0]))
		value = utils.normalize(entry[1])
		# store it into the new database
		if debug: print "[HISTORY]["+key_to+"] ("+utils.timestamp2date(timestamp)+") "+str(value)
		db.set(key_to,value,timestamp)
		count = count +1
	print "\t\tdone, "+str(count)+" values"

# for each recent key to migrate
print "Migrating recent data..."
for key_from in recent:
	if not migrate_recent: break
	key_to = recent[key_from]
	print "\tMigrating "+key_from+" -> "+key_to
	# retrieve the recent data
        change_db(db_from)
        data = db.rangebyscore(key_from,utils.now()-2*conf["constants"]["1_day"],utils.now(),withscores=True)
        change_db(db_to)
        count = 0
        # for each entry
        for entry in data:
                timestamp = utils.timezone(entry[0])
                value = utils.normalize(entry[1])
		if debug: print "[RECENT]["+key_to+"] ("+utils.timestamp2date(timestamp)+") "+str(value)
                # skip it if the same value is already stored
                old = db.rangebyscore(key_to,timestamp,timestamp)
                if len(old) > 0: continue
		# store it into the new database
		db.set(key_to,value,timestamp)
		# create the sensor data structure
		key_split = key_to.split(":")
		group_id = key_split[-2]
		sensor_id = key_split[-1]
		module = 'weather'
	        sensor = conf['modules'][module]['sensor_groups'][group_id]['sensors'][sensor_id]
	        sensor['module'] = module
	        sensor['group_id'] = group_id
        	sensor['sensor_id'] = sensor_id
	        sensor['features'] = conf["constants"]["sensor_features"][sensor["request"]]
	        sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module"]+":sensors:"+sensor["group_id"]
	        sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
		sensors.summarize(sensor,'hour',utils.hour_start(timestamp),utils.hour_end(timestamp))
                count = count +1
        print "\t\tdone, "+str(count)+" values"







