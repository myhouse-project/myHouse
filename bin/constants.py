#!/usr/bin/python
import logging
import os

hour = 60*60
day = 24*hour
milliseconds = 1

db_schema = {}
db_schema["root"] = "myHouse"
db_null = "None"

modules_with_sensors = ['weather']

log_formatter = logging.Formatter('[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s',"%Y-%m-%d %H:%M:%S")
log_path = os.path.abspath(os.path.dirname(__file__))+"/../logs/"
log_file = log_path+"myHouse.log"

sensor_measures = {
	'weather_forecast': {
		'avg': False,
		'min_max': False,
	},
	'weather_alerts': {
                'avg': False,
                'min_max': False,
	},
	'temperature': {
                'avg': True,
                'min_max': True,
	},
	'weather_condition': {
                'avg': True,
                'min_max': False,
	},
	'temperature_record:min': {
                'avg': False,
                'min_max': False,
	},
	'temperature_record:max': {
                'avg': False,
                'min_max': False,
        },
	'temperature_normal:min': {
		'avg': False,
                'min_max': False,
	},
        'temperature_normal:max': {
                'avg': False,
                'min_max': False,
        },
}
