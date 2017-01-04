#!/usr/bin/python
import sys
import os
import subprocess
import requests
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import time
import math
import traceback
import datetime
import numpy
import random
import __builtin__
from math import radians, cos, sin, asin, sqrt

import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# remove all occurences of value from array
def remove_all(array,value):
        return [x for x in array if x != value]

# return the current offset from utc time
def get_utc_offset():
	is_dst = time.daylight and time.localtime().tm_isdst > 0
	utc_offset = - (time.altzone if is_dst else time.timezone)
	return int(utc_offset/3600)

# return the timestamp with a the timezone offset applied
def timezone(timestamp):
	return int(timestamp+get_utc_offset()*conf["constants"]["1_hour"])

# return an UTC timestamp from a local timezone timestamp
def utc(timestamp):
	return int(timestamp-get_utc_offset()*conf["constants"]["1_hour"])

# return the now timestamp (in the local timezone)
def now():
	return timezone(int(time.time()))

# return yesterday's timestamp (in the local timezone)
def yesterday():
	return now()-24*conf["constants"]["1_hour"]

# return the last hour timestamp
def last_hour():
	return now()-60*conf["constants"]["1_minute"]

# generate a given timestamp based on the input (in the local timezone)
def get_timestamp(years,months,days,hours,minutes,seconds):
	timestamp = datetime.datetime(years,months,days,hours,minutes,seconds,0)
	return timezone(int(time.mktime(timestamp.timetuple())))

# return day start timestamp
def day_start(timestamp):
	date = datetime.datetime.fromtimestamp(utc(timestamp))
	return get_timestamp(date.year,date.month,date.day,0,0,0)

# return day end timestamp
def day_end(timestamp):
        date = datetime.datetime.fromtimestamp(utc(timestamp))
        return get_timestamp(date.year,date.month,date.day,23,59,59)

# return hour start timestamp
def hour_start(timestamp):
        date = datetime.datetime.fromtimestamp(utc(timestamp))
        return get_timestamp(date.year,date.month,date.day,date.hour,0,0)

# return hour end timestamp
def hour_end(timestamp):
        date = datetime.datetime.fromtimestamp(utc(timestamp))
        return get_timestamp(date.year,date.month,date.day,date.hour,59,59)

# return the realtime timestamp
def realtime(hours=conf["general"]["timeframes"]["realtime_hours"]):
	return now()-hours*conf["constants"]["1_hour"]

# return the recent timestamp
def recent(hours=conf["general"]["timeframes"]["recent_hours"]):
	return now()-hours*conf["constants"]["1_hour"]

# return the history timestamp
def history(days=conf["general"]["timeframes"]["history_days"]):
	return now()-days*conf["constants"]["1_day"]

# return a timestamp as a human readable format
def timestamp2date(timestamp):
        return datetime.datetime.fromtimestamp(utc(int(timestamp))).strftime('%Y-%m-%d %H:%M:%S')

# return the difference between two timestamps in a human readable format
def timestamp_difference(date1,date2):
        seconds = math.floor(math.fabs(date1-date2))
        interval = math.floor(seconds / 31536000)
        if interval > 1: return str(int(interval)) + " years ago"
        interval = math.floor(seconds / 2592000)
        if interval > 1: return str(int(interval)) + " months ago"
        interval = math.floor(seconds / 86400)
        if interval > 1: return str(int(interval)) + " days ago"
        interval = math.floor(seconds / 3600)
        if interval > 1: return str(int(interval)) + " hours ago"
        interval = math.floor(seconds / 60)
        if interval > 1: return str(int(interval)) + " minutes ago"
        return str(int(math.floor(seconds))) + " seconds ago"

# convert a string into a timestamp
def string2timestamp(string):
	if "s" in string: return now()-int(string.replace("s",""))
	elif "m" in string: return now()-int(string.replace("m",""))*60
	elif "h" in string: return now()-int(string.replace("d",""))*60*60
	elif "d" in string: return now()-int(string.replace("h",""))*60*60*24

# return true if the input is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# normalize the value. If the input is a number, keep a single digit, otherwise return a string
def normalize(value,formatter=None):
	if value == conf["constants"]["null"]: return conf["constants"]["null"]
	if formatter is None:
		return float("{0:.1f}".format(float(value))) if is_number(value) else str(value)
	elif formatter == "int": return int(float(value))
	elif formatter == "float_1": return float("{0:.1f}".format(float(value)))
	elif formatter == "float_2": return float("{0:.2f}".format(float(value)))
	else: return str(value)

# request a given url
def web_get(url,username=None,password=None,binary=False,params={}):
	log.debug("Requesting web page "+url)
	if username is not None: request = requests.get(url,params=params,auth=(username,password),timeout=conf['constants']['web_timeout'],verify=False)
	else: request = requests.get(url,params=params,timeout=conf['constants']['web_timeout'],verify=False)
	if binary: return request.content
	else: return request.text

# calculate the min of a given array of data
def min(data):
	data = remove_all(data,None)
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.min(data)
		else: return None
	else: return None

# calculate the max of a given array of data
def max(data):
	data = remove_all(data,None)
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.max(data)
		else: return None
	else: return None

# calculate the avg of a given array of data
def avg(data):
	data = remove_all(data,None)
	if len(data) > 0:
		if is_number(data[0]): return normalize(numpy.mean(data))
		else: return __builtin__.max(set(data), key=data.count)
	else: return None

# return the exception as a string
def get_exception(e):
	etype, value, tb = sys.exc_info()
	error = ''.join(traceback.format_exception(etype, value, tb,None))
	return error.replace('\n','|')

# return a random int between min and max
def randint(min,max):
	return random.randint(min,max)

# truncate a long string 
def truncate(string):
	max_len = 50
	return (string[:max_len] + '...') if len(string) > max_len else string

# return a dict merging delta into template
def merge(template,delta):
	new_dict = template.copy()
	new_dict.update(delta)

# return a given module
def get_module(module_id):
	if "modules" not in conf: return None
	for i in range(len(conf["modules"])):
		module = conf["modules"][i]
		if module["module_id"] == module_id: return module

# return a given sensor group
def get_group(module_id,group_id):
	module = get_module(module_id)
	if module is None: return None
	if "sensors" not in module: return None
	sensors = []
	for i in range(len(module["sensors"])):
		sensor = module["sensors"][i]
		sensor["module_id"] = module_id
		if sensor["group_id"] == group_id: sensors.append(sensor)
	return sensors

# return a given sensor
def get_sensor(module_id,group_id,sensor_id):
	sensors = get_group(module_id,group_id)
	if sensors is None: return None
	for j in range (len(sensors)):
		sensor = sensors[j]
		if sensor["sensor_id"] == sensor_id: return sensor
	return None

# split a given group string
def split_group(widget,key):
        # ensure the key is in widget
        if key not in widget:
                log.warning("Unable to find "+key+" in widget "+widget["widget_id"])
                return None
        # split it
        split = widget[key].split(":")
        # ensure the group exists
        group = get_group(split[0],split[1])
	if group is None:
        	log.warning("Unable to find group "+key+" for widget "+widget["widget_id"])
                return None
	return split

# split a given sensor string
def split_sensor(widget,key):
        # ensure the key is in widget
        if key not in widget:
                log.warning("Unable to find "+key+" in widget "+widget["widget_id"])
                return None
        # split it
	split = widget[key].split(":")
        # ensure the sensor exists
        sensor = get_sensor(split[0],split[1],split[2])
        if sensor is None:
        	log.warning("Unable to find sensor "+key+" for widget "+widget["widget_id"])
                return None
        return split

# run a command and return the output
def run_command(command,timeout=conf["constants"]["linux_timeout"],shell=True):
        log.debug("Executing "+str(command))
        process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
	for t in xrange(timeout):
		time.sleep(1)
		if process.poll() is not None:
			for line in process.stdout.readlines():
				output = output+line
			return output.rstrip()
	process.kill()
	return ""

# determine if it is night
def is_night():
        is_night = False
        hour = int(time.strftime("%H"))
        if hour >= 20 or hour <= 6: is_night = True;
	return is_night

# convert the temperature if needed
def temperature_unit(temperature,force=False):
	if conf["general"]["units"]["fahrenheit"] or force: return (temperature * 1.8) + 32
	else: return temperature

# convert a length if neeeded
def length_unit(length,force=False):
        if conf["general"]["units"]["imperial"] or force: return length*0.039370
        else: return length

# convert a pressure if neeeded
def pressure_unit(pressure,force=False):
        if conf["general"]["units"]["imperial"] or force: return (29.92 * pressure) / 1013.25
        else: return pressure

# convert a speed if needed
def speed_unit(speed,force=False):
	if conf["general"]["units"]["imperial"] or force: return speed*0.621371
	else: return speed

# return the file path of a given widget id
def get_widget_chart(widget_id):
	return conf['constants']['tmp_dir']+'/chart_'+widget_id+'.'+conf['constants']['chart_extension']


# return the distance in km between two coordinates
def distance(a,b):
	if len(a) != 2 or len(b) != 2: return 0
	lat1 = a[0]
	lon1 = a[1]
	lat2 = b[0]
	lon2 = b[1]
	# convert decimal degrees to radians 
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	km = 6367 * c
	return length_unit(km)

# check if a file exists on the filesystem
def file_exists(file):
	return os.path.isfile(file)
