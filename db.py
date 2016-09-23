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
		log.debug("connecting to DB: "+str(db))
		db = redis.StrictRedis(host=conf['db']['hostname'], port=conf['db']['port'], db=conf['db']['database'])
	if not conf['db']['enabled']: log.warning("Database writing disabled")
	return db

# normalize the output
def normalize_dataset(data,withscores,milliseconds,format_date):
	output = []
	for entry in data:
		# get the timestamp 
		timestamp = int(entry[1])
		if format_date: timestamp = utils.timestamp2date(timestamp)
		elif milliseconds: timestamp = timestamp*1000
		# normalize the value (entry is timetime:value)
		value_string = entry[0].split(":",1)[1];
		# cut the float if a number of make it string
		value = float(value_string) if utils.is_number(value_string) else str(value_string)
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

# save a value to the db (both with and without timestamp)
def set(key,value,timestamp):
	db = connect()
	# simple set query
	if timestamp is None: 
		log.debug("set "+key+" "+str(value))
		if not conf['db']['enabled']: return 0
		return db.set(key,value)
	# zadd with the score	
	else: 
		value = str(timestamp)+":"+str(value)
		log.debug("zadd "+key+" "+str(timestamp)+" "+str(value))
		if not conf['db']['enabled']: return 0
		return db.zadd(key,timestamp,value)

# get a single value from the db
def get(key):
        db = connect()
	log.debug("get "+key)
	return db.get(key)

# get a range of values from the db based on the timestamp
def rangebyscore(key,start=utils.recent(),end=utils.now(),withscores=True,milliseconds=False,format_date=False):
	db = connect()
	log.debug("zrangebyscore "+key+" "+str(start)+" "+str(end))
	return normalize_dataset(db.zrangebyscore(key,start,end,withscores=True),withscores,milliseconds,format_date)
	
# get a range of values from the db
def range(key,start=-1,end=-1,withscores=True,milliseconds=False,format_date=False):
        db = connect()
        log.debug("zrange "+key+" "+str(start)+" "+str(end))
        return normalize_dataset(db.zrange(key,start,end,withscores=True),withscores,milliseconds,format_date)

# delete a key
def delete(key):
	db = connect()
        log.debug("del "+key)
        return db.delete(key)

# delete all elements between a given score
def deletebyscore(key,start,end):
	db = connect()
	log.debug("zremrangebyscore "+key+" "+str(start)+" "+str(end))
	return db.zremrangebyscore(key,start,end)

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
	version_key = conf["constants"]["db_schema"]["root"]+":version"
	if not exists(version_key): set(version_key,conf["constants"]["version"],None)
	else:
		version = float(get(version_key))
		if version != conf["constants"]["version"]: log.warning("database version mismatch (expecting v"+str(conf["constants"]["version"])+" but found v"+str(version)+")")

# main
if __name__ == '__main__':
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
		print "\t- "+key+": "+str(db.zcard(key))
	
