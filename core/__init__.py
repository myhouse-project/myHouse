#!/usr/bin/python
import sys
import os
import logging
import requests
import time

# constants
hour = 60*60
day = 24*hour
milliseconds = 1
sensors_expire = 60

# load the configuration
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)

logger = logging.getLogger("myHouse")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def get_logger(name):
	return logger

def get_config():
	return config


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

def get_json(url):
	return requests.get(url).json()
