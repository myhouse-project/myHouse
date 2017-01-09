#!/usr/bin/python
import datetime
import time
import feedparser
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# poll the sensor
def poll(sensor):
	# query the service
	data = utils.web_get(sensor["plugin"]["url"])
	return json.dumps(data)

# parse the data
def parse(sensor,data):
	# load the file
	data = json.loads(data)
	# parse the feed
	feed = feedparser.parse(data)
	result = ""
	for i in range(len(feed["entries"])):
		entry = feed["entries"][i]
		# return a single string containing all the entries
		result = result + entry["title"].encode('ascii','ignore')+"\n"
	return result

# return the cache schema
def cache_schema(sensor):
	# cache the entire file
	return sensor["plugin"]["url"]

