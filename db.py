#!/usr/bin/python
import sys
import os
import redis

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# initialize the connection
db = None

# connect to the db if not connected yet
def connect():
	global db
	if db is None: 
		db = redis.StrictRedis(host=conf['db']['hostname'], port=conf['db']['port'], db=conf['db']['database'])
		log.debug("connected to DB: "+str(db))
	if not conf['db']['enabled']: log.warning("Database writing disabled")
	return db

# normalize the output
def normalize_dataset(data,withscores,milliseconds,format_date,formatter):
	output = []
	for entry in data:
		# get the timestamp 
		timestamp = int(entry[1])
		if format_date: timestamp = utils.timestamp2date(timestamp)
		elif milliseconds: timestamp = timestamp*1000
		# normalize the value (entry is timetime:value)
		value_string = entry[0].split(":",1)[1];
		if formatter is None:
			# no formatter provided, guess the type
			value = float(value_string) if utils.is_number(value_string) else str(value_string)
		else:
			# formatter provided, normalize the value
			value = utils.normalize(value_string,formatter)
		# normalize "None" in null
		if value == conf["constants"]["null"]: value = None
		# prepare the output
		if (withscores): output.append([timestamp,value])
		else: output.append(value)
	return output

# show the available keys applying the given filter
def keys(key):
	db = connect()
	log.debug("keys "+key)
	return db.keys(key)

# save a value to the db
def set(key,value,timestamp):
	db = connect()
	if timestamp is None: 
		log.warning("no timestamp provided for key "+key)
		return 
	# zadd with the score	
	value = str(timestamp)+":"+str(value)
	log.debug("zadd "+key+" "+str(timestamp)+" "+str(value))
	if not conf['db']['enabled']: return 0
	return db.zadd(key,timestamp,value)

# set a single value into the db
def set_simple(key,value):
        db = connect()
        log.debug("set "+str(key))
        db.set(key,str(value))

# get a single value from the db
def get(key):
        db = connect()
	log.debug("get "+key)
	return db.get(key)

# get a range of values from the db based on the timestamp
def rangebyscore(key,start=utils.recent(),end=utils.now(),withscores=True,milliseconds=False,format_date=False,formatter=None):
	db = connect()
	log.debug("zrangebyscore "+key+" "+str(start)+" "+str(end))
	return normalize_dataset(db.zrangebyscore(key,start,end,withscores=True),withscores,milliseconds,format_date,formatter)
	
# get a range of values from the db
def range(key,start=-1,end=-1,withscores=True,milliseconds=False,format_date=False,formatter=None):
        db = connect()
        log.debug("zrange "+key+" "+str(start)+" "+str(end))
        return normalize_dataset(db.zrange(key,start,end,withscores=True),withscores,milliseconds,format_date,formatter)

# delete a key
def delete(key):
	db = connect()
        log.debug("del "+key)
        return db.delete(key)

# rename a key
def rename(key,new_key):
        db = connect()
        log.debug("rename "+key+" "+new_key)
        return db.rename(key,new_key)

# delete all elements between a given score
def deletebyscore(key,start,end):
	db = connect()
	log.debug("zremrangebyscore "+key+" "+str(start)+" "+str(end))
	return db.zremrangebyscore(key,start,end)

# delete all elements between a given rank
def deletebyrank(key,start,end):
        db = connect()
        log.debug("zremrangebyrank "+key+" "+str(start)+" "+str(end))
        return db.zremrangebyrank(key,start,end)

# check if a key exists
def exists(key):
        db = connect()
        log.debug("exists "+key)
        return db.exists(key)

# empty the database
def flushdb():
        db = connect()
        log.debug("flushdb")
        return db.flushdb()

# initialize an empty database
def init():
	db = connect()
	# check the version
	version_key = conf["constants"]["db_schema"]["version"]
	if not exists(version_key): 
		set_simple(version_key,conf["constants"]["version"])
		return True
	else:
		version = float(get(version_key))
		if version != conf["constants"]["version"]: 
			log.error("run the upgrade.py script first to upgrade the database (expecting v"+str(conf["constants"]["version"])+" but found v"+str(version)+")")
			return False
	return True

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		# print database status and a summary of all the keys
		connect()
		print "Connection: "+str(db)
		print "\nDatabase info:"
		info = db.info()
		for key in info:
			print "\t- "+key+": "+str(info[key])
		print "\nDatabase key size:"
		keys = keys("*")
		for key in sorted(keys):
			if db.type(key) != "zset": continue
			data = range(key,1,1,format_date=True)
			start = data[0][0] if len(data) > 0 else "N.A"
	               	data = range(key,-1,-1,format_date=True)
			end = data[0][0] if len(data) > 0 else "N.A"
			print "\t- "+key+": "+str(db.zcard(key))+" ("+start+" / "+end+")"
	
	else:
		if sys.argv[1] == "delete": 
			key = conf["constants"]["db_schema"]["root"]+":"+sys.argv[2]
			print "Deleting sensor "+key
			delete(key)
			delete(key+":hour:min")
			delete(key+":hour:avg")
			delete(key+":hour:max")
			delete(key+":hour:rate")
			delete(key+":day:min")
                        delete(key+":day:avg")
                        delete(key+":day:max")
			delete(key+":day:rate")
		elif sys.argv[1] == "rename":
			key = conf["constants"]["db_schema"]["root"]+":"+sys.argv[2]
			new_key = conf["constants"]["db_schema"]["root"]+":"+sys.argv[3]
			print "Renameing sensor "+key+" into "+new_key
			rename(key,new_key)
			rename(key+":hour:min",new_key+":hour:min")
                        rename(key+":hour:avg",new_key+":hour:avg")
                        rename(key+":hour:max",new_key+":hour:max")
			rename(key+":hour:rate",new_key+":hour:rate")
                        reanme(key+":day:min",new_key+":day:min")
                        rename(key+":day:avg",new_key+":day:avg")
                        rename(key+":day:max",new_key+":day:max")
			rename(key+":day:rate",new_key+":day:rate")
		else: print "Usage: "+__file__+" <delete|rename> <module_id:group_id:sensor_id> [module_id:group_id:new_sensor_id]"
