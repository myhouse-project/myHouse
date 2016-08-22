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
	'sensor_features': {
		'weather_forecast': {
			'format': 'string',
                        'calculate_avg': False,
                        'calculate_min_max': False,
                        'show_avg': False,
                        'show_min_max': False,
		},
		'weather_alerts': {
			'format': 'string',
	                'calculate_avg': False,
	                'calculate_min_max': False,
                        'show_avg': False,
                        'show_min_max': False,
		},
		'temperature': {
			'format': 'float',
	                'calculate_avg': True,
	                'calculate_min_max': True,
			'show_current': True,
                        'show_avg': True,
                        'show_min_max': True,
		},
		'weather_condition': {
			'format': 'string',
        	        'calculate_avg': True,
	                'calculate_min_max': False,
			'show_current': True,
                        'show_avg': True,
                        'show_min_max': False,
		},
		'temperature_record': {
			'format': 'float',
        	        'calculate_avg': False,
	                'calculate_min_max': False,
			'show_current': False,
                        'show_avg': False,
                        'show_min_max': True,
		},
		'temperature_normal': {
			'format': 'float',
			'calculate_avg': False,
	                'calculate_min_max': False,
			'show_current': False,
                        'show_avg': False,
                        'show_min_max': True,
		},
	},
}

# return all the configuration settings as an object
def get_constants():
    return constants

