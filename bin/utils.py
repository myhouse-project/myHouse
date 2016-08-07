#!/usr/bin/python
import sys
import os
import requests
import time
import traceback
import datetime
import numpy
import random
import __builtin__

import constants
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# remove all occurences of value from array
def remove_all(array,value):
        return [x for x in array if x != value]

# return the timestamp with a the timezone offset applied
def timezone(timestamp):
	return int(timestamp+conf["general"]["timezone_offset_hours"]*constants.hour)

# return an UTC timestamp from a local timezone timestamp
def utc(timestamp):
	return int(timestamp-conf["general"]["timezone_offset_hours"]*constants.hour)

# return the now timestamp
def now():
	return timezone(int(time.time()))

# return yesterday's timestamp
def yesterday():
	return now()-24*constants.hour

# return the last hour timestamp
def last_hour():
	return now()-60*constants.minute

# generate a given timestamp based on the input
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

# return the recent timestamp (default: last 24 hours)
def recent():
	return now()-24*constants.hour

# return the history timestamp (default: last 1 year)
def history():
	return now()-365*constants.day

# return true if the input is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# normalize the value. If the input is a number, keep a single digit, otherwise return a string
def normalize(value):
	return float("{0:.1f}".format(float(value))) if is_number(value) else str(value)

# request a given url
def get(url):
	log.debug("Requesting web page "+url)
	return requests.get(url).text

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
	return traceback.format_exc(e)

# return a random int between min and max
def randint(min,max):
	return random.randint(min,max)

# return a timestamp as a human readable format
def timestamp2date(timestamp):
	return datetime.datetime.fromtimestamp(utc(int(timestamp))).strftime('%Y-%m-%d %H:%M:%S')

