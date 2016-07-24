#!/usr/bin/python
import sys
import os
import requests
import time

# constants
hour = 60*60
day = 24*hour
milliseconds = 1
sensors_expire = 60

def now():
	return int(time.time())*milliseconds

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
	return requests.get(url).text
