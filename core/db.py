#!/usr/bin/python
import sys
import os
import redis

sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../")
import core
logger = core.get_logger(__name__)
config = core.get_config()

schema = {}
schema["root"] = "myHouse"
schema["sensors"] = schema["root"]+":sensors"
schema["sensors_cache"] = schema["sensors"]+":cache"

db = None

# connect to the db if not connected yet
def connect():
	global db
	if db is None: 
		db = redis.StrictRedis(host=config["db_hostname"], port=config["db_port"], db=config["db_number"])
		logger.debug("connected to DB: "+str(db))
	return db

# normalize the output
def normalize(data,withscores):
	output = []
	for entry in data:
		# get the timestamp 
		timestamp = int(entry[1])*core.milliseconds
		# get the value
		value_string = entry[0].split(":",1)[1];
		value = core.normalize(value_string)
		# prepare the output
		if (withscores): output.append([timestamp,value])
		else: output.append(value)
	return output

# show the avaialble keys applying the given filter
def keys(key):
	db = connect()
	logger.debug("keys "+key)
	return db.keys(key)


# save a value to the db
def set(key,value,timestamp):
	db = connect()
	# simple set query
	if timestamp is None: 
		logger.debug("set "+key+" "+str(value))
		if not config["db_write"]: return 0
		return db.set(key,value)
	# zadd with the score	
	else: 
		value = str(timestamp)+":"+str(value)
		logger.debug("zadd "+key+" "+str(timestamp)+" "+str(value))
		if not config["db_write"]: return 0
		return db.zadd(key,timestamp,value)

# get a single value from the db
def get(key):
        db = connect()
	logger.debug("get "+key)
	return db.get(key)

# get a range of values from the db based on the score
def rangebyscore(key,start=core.recent(),end=core.now(),withscores=True):
	db = connect()
	logger.debug("zrangebyscore "+key+" "+str(start)+" "+str(end))
	return normalize(db.zrangebyscore(key,start,end,withscores=True),withscores)
	

# get a range of values from the db
def range(key,start=-1,end=-1,withscores=True):
        db = connect()
        logger.debug("zrange "+key+" "+str(start)+" "+str(end))
        return normalize(db.zrange(key,start,end,withscores=True),withscores)

# delete a key
def delete(key):
	db = connect()
        logger.debug("del "+key)
        return db.delete(key)

# check if a key exists
def exists(key):
        db = connect()
        logger.debug("exists "+key)
        return db.exists(key)

