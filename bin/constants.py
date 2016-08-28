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
	'web_timeout': 10,
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
		'master': {
			'chart': {
			},
			'title': {
				'text': '',
			},
			'xAxis': {
			},
			'yAxis': {
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
			'tooltip': {
				'shared': True,
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
		'chart_short': {
			'template': 'master',
			'chart': {
				'height': 194,
			},
			'xAxis': {
				'type': 'datetime',
			},
			'yAxis': {
				'title': '',
			},
		},
		'chart_short_inverted': {
			'template': 'chart_short',
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
		},
		'chart_summary': {
			'template': 'master',
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
			'series': [
				{
					'name': 'Yesterday',
					'color': 'rgb(169,255,150)',
					'pointWidth': 18,
					'dataLabels': {
						'enabled': False,
					},
				},
				{
					'name': 'Today',
					'color': '#7cb5ec',
					'pointWidth': 10,
				},
			],
		},
		'chart_history': {
			'template': 'master',
			'chart': {
				'type': 'spline',
				'zoomType': 'x',
			},
			'xAxis': {
				'type': 'datetime',
				'tickInterval': 1*24*3600*1000,
				'tickWidth': 0,
				'gridLineWidth': 1,
			},
		},
		'chart_recent': {
			'template': 'chart_history',
			'xAxis': {
				'type': 'datetime',
				'tickInterval': 1*3600*1000,
				'tickWidth': 0,
				'gridLineWidth': 1,
			},
			'rangeSelector': {
				'enabled': False,
			},
		},		
	},
}
# merge the chart template with the deltas
for chart_id in constants['charts']:
	chart = constants['charts'][chart_id]
	if 'template' not in chart: continue
	new_chart = constants['charts'][chart['template']].copy()
	new_chart.update(chart)
	constants['charts'][chart_id] = new_chart

# return all the configuration settings as an object
def get_constants():
	is_night = False
	hour = int(time.strftime("%H"))
	if hour >= 20 or hour <= 6: is_night = True;
	constants['is_night'] = is_night
	return constants
