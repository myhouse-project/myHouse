#!/usr/bin/python

import logging

import utils
import db
import config
conf = config.get_config()
import sensors

######## START OF CONFIGURATION
# variables
empty_target_db = False
migrate_history = True
history_start_timestamp = "-inf"
history_end_timestamp = utils.now()
migrate_recent = True

# database number from which we are migrating
db_from = 0
# database number into which we are migrating
db_to = 1

# keys to migrate history (from key -> to key)
# destination key format: myHouse:<module_id>:<group_id>:<sensor_id>
history = {
	'home:weather:outdoor:temperature:day:max': 'myHouse:outdoor:temperature:external:day:max',
	'home:weather:outdoor:temperature:day:min': 'myHouse:outdoor:temperature:external:day:min',
	'home:weather:outdoor:temperature:day': 'myHouse:outdoor:temperature:external:day:avg',

        'home:weather:indoor:temperature:day:max': 'myHouse:indoor:temperature:living_room:day:max',
        'home:weather:indoor:temperature:day:min': 'myHouse:indoor:temperature:living_room:day:min',
        'home:weather:indoor:temperature:day': 'myHouse:indoor:temperature:living_room:day:avg',

	'home:weather:almanac:record:min': 'myHouse:outdoor:temperature:record:day:min',
	'home:weather:almanac:record:max': 'myHouse:outdoor:temperature:record:day:max',

        'home:weather:almanac:normal:min': 'myHouse:outdoor:temperature:normal:day:min',
        'home:weather:almanac:normal:max': 'myHouse:outdoor:temperature:normal:day:max',

	'home:weather:outdoor:condition:day': 'myHouse:outdoor:temperature:condition:day:avg',
}

# keys to migrate recent data (from key -> to key)
recent = {
	'home:weather:outdoor:temperature:measure': 'myHouse:outdoor:temperature:external',
	'home:weather:indoor:temperature:measure': 'myHouse:indoor:temperature:living_room',
	'home:weather:outdoor:condition:measure': 'myHouse:outdoor:temperature:condition',
}

#debug
debug = False
######## END OF CONFIGURATION

# change into a given database number
def change_db(database):
	db.db = None
	conf['db']['database'] = database

# empty the target database first
if empty_target_db:
	print "Flushing target database..."
	change_db(db_to)
	db.flushdb()

# for each history key to migrate
print "Migrating historical data..."
for key_from in history:
	if not migrate_history: break
	key_to = history[key_from]
	print "\tMigrating "+key_from+" -> "+key_to
	# retrieve all the data
	change_db(db_from)
	data = db.rangebyscore(key_from,history_start_timestamp,history_end_timestamp,withscores=True)
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
		module_id = key_split[-4]
	        sensor = utils.get_sensor(module_id,group_id,sensor_id)
	        sensor['module_id'] = module_id
	        sensor['group_id'] = group_id
	        sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module_id"]+":"+sensor["group_id"]
	        sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
		sensors.summarize(sensor,'hour',utils.hour_start(timestamp),utils.hour_end(timestamp))
                count = count +1
        print "\t\tdone, "+str(count)+" values"







