#!/usr/bin/python
import sys
import os
import requests
import time
import datetime
import numpy
import __builtin__
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()

# constants
hour = 60*60
day = 24*hour
milliseconds = 1
sensors_expire = 60

def now():
	return int(time.time())*milliseconds

def last_day_start():
	last = datetime.datetime.now() - datetime.timedelta(days = 1)
	last_beginning = datetime.datetime(last.year, last.month, last.day,0,0,0,0)
	return int(time.mktime(last_beginning.timetuple()))

def last_day_end():
	last = datetime.datetime.now() - datetime.timedelta(days = 1)
	last_end = datetime.datetime(last.year, last.month, last.day,23,59,59,999)
	return int(time.mktime(last_end.timetuple()))

def last_hour_start():
        last = datetime.datetime.now() - datetime.timedelta(hours = 1)
        last_beginning = datetime.datetime(last.year, last.month, last.day,last.hour,0,0,0)
        return int(time.mktime(last_beginning.timetuple()))


def last_hour_end():
        last = datetime.datetime.now() - datetime.timedelta(hours = 1)
        last_end = datetime.datetime(last.year, last.month, last.day,last.hour,59,59,999)
        return int(time.mktime(last_end.timetuple()))

def recent():
	return now()-24*hour*milliseconds

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def normalize(value):
	return float("{0:.1f}".format(float(value))) if is_number(value) else str(value)

def get(url):
	logger.debug("Requesting web page "+url)
	return requests.get(url).text


def min(data):
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.min(data)
		else: return None
	else: return None

def max(data):
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.max(data)
		else: return None
	else: return None

def avg(data):
	if len(data) > 0:
		if is_number(data[0]): return numpy.mean(data)
		else: return max(set(data), key=data.count)
	else: return None
