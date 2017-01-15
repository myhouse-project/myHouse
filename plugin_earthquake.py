#!/usr/bin/python
import datetime
import time
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

if 'earthquake' in conf['plugins']: plugin_conf = conf['plugins']['earthquake']
limit = 10000
query = "format=text&limit="+str(limit)+"&orderby=time-asc"

# poll the sensor
def poll(sensor):
	# query the service
	url = "http://"+sensor["plugin"]["domain"]+"/fdsnws/event/1/query?"+query+"&"+str(sensor["plugin"]["query"])
	data = utils.web_get(url)
	return json.dumps(data)

# parse the data
def parse(sensor,data):
	measures = []
	measure = {}
	# load the file
	data = json.loads(data)
	# for each line
	for line in data.split('\n'):
		#EventID|Time|Latitude|Longitude|Depth/Km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName
		#    0    1      2          3       4       5     6           7            8           9     10         11           12
		if line.startswith('#'): continue
		measure = {}
		# split the entries
		entry = line.split('|')
		if len(entry) != 13: continue
		# set the timestamp to the event's date
		date_format = "%Y-%m-%dT%H:%M:%S.%f"
		date = datetime.datetime.strptime(entry[1],date_format)
		measure["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
		# prepare the position value
		position = {}
		position["latitude"] = float(entry[2])
		position["longitude"] = float(entry[3])
		position["label"] = str(entry[10])
		date_string = utils.timestamp2date(int(measure["timestamp"]))
#		position["text"] = str("<p><b>"+entry[12]+":</b></p><p>Magnitude: "+entry[10]+"</p><p>Date: "+date_string+"</p><p>Depth: "+entry[4]+" km</p>")
		position["text"] = str(entry[12])
		# prepare the measure
		measure["key"] = sensor["sensor_id"]+":day:avg"
		measure["value"] = json.dumps(position)
		# add the event to the measures
		measures.append(measure)
	return measures

# return the cache schema
def cache_schema(sensor):
	# cache the entire file
	return sensor["plugin"]["domain"]

