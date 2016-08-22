#!/usr/bin/python
import logging
import os

# constants
constants = {
	'version': 1.1,
	'1_minute': 60,
	'1_hour': 3600,
	'1_day': 86400,
	'db_schema': {
		'root': "myHouse",
	},
	'null': "None",
	'logging': {
                'path': os.path.abspath(os.path.dirname(__file__))+"/../logs/",
                'logfile': os.path.abspath(os.path.dirname(__file__))+"/../logs/myHouse.log",
		'formatter': logging.Formatter('[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s',"%Y-%m-%d %H:%M:%S"),
	},
}

# return all the configuration settings as an object
def get_constants():
    return constants

