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

# return the now timestamp
def now():
	return int(time.time())*constants.milliseconds

# return last day start timestamp
def last_day_start():
	last = datetime.datetime.now() - datetime.timedelta(days = 1)
	last_beginning = datetime.datetime(last.year, last.month, last.day,0,0,0,0)
	return int(time.mktime(last_beginning.timetuple()))

# return last day end timestamp
def last_day_end():
	last = datetime.datetime.now() - datetime.timedelta(days = 1)
	last_end = datetime.datetime(last.year, last.month, last.day,23,59,59,999)
	return int(time.mktime(last_end.timetuple()))

# return last hour start timestamp
def last_hour_start():
        last = datetime.datetime.now() - datetime.timedelta(hours = 1)
        last_beginning = datetime.datetime(last.year, last.month, last.day,last.hour,0,0,0)
        return int(time.mktime(last_beginning.timetuple()))

# return last hour end timestamp
def last_hour_end():
        last = datetime.datetime.now() - datetime.timedelta(hours = 1)
        last_end = datetime.datetime(last.year, last.month, last.day,last.hour,59,59,999)
        return int(time.mktime(last_end.timetuple()))

# return the recent timestamp (default: last 24 hours)
def recent():
	return now()-24*constants.hour*constants.milliseconds

# return the history timestamp (default: last 1 year)
def history():
	return now()-365*constants.day*constants.milliseconds

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
