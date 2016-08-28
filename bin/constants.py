#!/usr/bin/python
import logging
import os
import time

# constants
constants = {
	'version': 1.1,
	'version_string': '1.1.0',
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
	'data_expire_days': 7,
	'cache_expire_min': 1,
	'formats': {
		'int': { 'unit': 'int', 'suffix': '', },
		'float': { 'unit': 'float', 'suffix': '', },
		'string': { 'unit': 'string', 'suffix': '', },
		'temperature': { 'unit': 'float', 'suffix': u'\u00B0C', },
		'size': { 'unit': 'int', 'suffix': 'MB', },
		'percentage': { 'unit': 'float', 'suffix': '%', },
		'precipitation_rain': { 'unit': 'int', 'suffix': 'mm', },
		'precipitation_snow': { 'unit': 'int', 'suffix': 'cm', },
		'image': { 'unit': "", 'suffix': "",},
	},
	'charts': {
		'template': {
			'chart': {
			},
			'title': {
				'text': '',
			},
			'xAxis': {
			},
			'credits': { 
				'enabled': False,
			},
			'legend': {
				'enabled': False,
			},
			'rangeSelector' : {
				'selected' : 0,
			},
			'plotOptions': {
				'spline': {
					'marker': {
						'enabled': True,
					},
					'lineWidth': 3,
					'dataLabels': {
						'enabled': True,
						'y': 40,
						'borderRadius': 5,
						'backgroundColor': 'rgba(252, 255, 197, 0.7)',
						'borderWidth': 1,
						'borderColor': '#AAA',
					},
				},
				'arearange': {
					'fillOpacity': 0.2,
					'lineWidth': 1,
					'color': '#7cb5ec',
				},				
				'columnrange': {
					'grouping': False,
					'shadow': False,
					'pointWidth': 10,
					'dataLabels': {
						'enabled': True,
					},					
				},
				'bar': {
					'pointWidth': 10,
					'dataLabels': { 
						'enabled': True, 
					},
				},
			},
		},
                'inverted_delta': {
                        'chart': {
                                'inverted': True,
                                'height': 194,
                        },
                        'xAxis': {
                                'type': 'datetime',
				'tickInterval': 24* 3600 * 1000,
                                'tickWidth': 0,
                                'gridLineWidth': 0,
                        },
                        'yAxis': {
                                'title': '',
                        },
                        'tooltip': {
                                'shared': True,
                        },
                        'series': [
                        ],
                },
		'min_max_delta': {
			'chart': {
				'type': 'columnrange',
				'inverted': True,
				'height': 194,
			},
			'xAxis': {
				'type': 'datetime',
				'categories': [],
			},
			'yAxis': {
				'title': '',
			},
			'tooltip': {
				'shared': True,
			},
			'series': [
				{
					'name': 'Yesterday',
					'color': 'rgb(169,255,150)',
					'pointWidth': 18,
				},
				{
					'name': 'Today',
					'color': '#7cb5ec',
					'pointWidth': 10,
					'dataLabels': {
						'enabled': True,
					},
				},
			],
		},
		'timeline_recent_delta': {
			'chart': {
				'type': 'spline',
				'zoomType': 'x',
			},
			'xAxis': {
				'type': 'datetime',
				'tickInterval': 1* 3600 * 1000,
				'tickWidth': 0,
				'gridLineWidth': 1,
			},
			'navigator': {
				'enabled': False,
			},
			'rangeSelector': {
				'enabled': False,
			},
		},
		'timeline_history_delta': {
			'chart': {
				'type': 'spline',
				'zoomType': 'x',
			},
			'xAxis': {
				'type': 'datetime',
				'tickInterval': 1*24* 3600 * 1000,
				'tickWidth': 0,
				'gridLineWidth': 1,
			},
		},
	},
}
# merge the chart template with the deltas
constants['charts']['min_max'] = constants['charts']['template'].copy()
constants['charts']['min_max'].update(constants['charts']['min_max_delta'])
constants['charts']['timeline_recent'] = constants['charts']['template'].copy()
constants['charts']['timeline_recent'].update(constants['charts']['timeline_recent_delta'])
constants['charts']['timeline_history'] = constants['charts']['template'].copy()
constants['charts']['timeline_history'].update(constants['charts']['timeline_history_delta'])
constants['charts']['inverted'] = constants['charts']['template'].copy()
constants['charts']['inverted'].update(constants['charts']['inverted_delta'])

# return all the configuration settings as an object
def get_constants():
	is_night = False
	hour = int(time.strftime("%H"))
	if hour >= 20 or hour <= 6: is_night = True;
	constants['is_night'] = is_night
	return constants
