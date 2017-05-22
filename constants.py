#!/usr/bin/python
import logging
import os
import time

base_dir = os.path.abspath(os.path.dirname(__file__))

# constants
constants = {
	'version': "2.4",
	'1_minute': 60,
	'1_hour': 3600,
	'1_day': 86400,
	'db_schema': {
		'root': "myHouse",
		'alerts': "myHouse:_alerts_",
		'tmp': "myHouse:_tmp_",
		'version': "myHouse:_version_",
	},
	'null': "None",
	'base_dir': base_dir,
	'log_dir': base_dir+"/logs",
	'tmp_dir': base_dir+"/tmp",
	'config_file': base_dir+"/config.json",
	'config_file_backup': base_dir+"/config.bak",
	'config_file_example': base_dir+"/config-example.json",
	'config_file_schema': base_dir+"/config-schema.json",
	'email_template': base_dir+"/template_email.html",
	'service_template': base_dir+"/template_service.sh",
	'service_location': '/etc/init.d/myhouse',
	'log_formatter': logging.Formatter('[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s',"%Y-%m-%d %H:%M:%S"),
	'image_unavailable': base_dir+"/web/images/image_unavailable.png",
	'web_dir': base_dir+"/web",
	'web_template': "template_web.html",
	'web_timeout': 20,
	'command_timeout': 30,
	'web_use_reloader': True,
	'bot_brain_file': base_dir+"/language",
	'chart_extension': 'png',
	'chart_short_height': 230,
	'image_detection_save_on_disk': True,
	'image_detection_max_saved_images': 10,
	'formats': {
		'int': { 
			'formatter': 'int', 
			'suffix': '', 
		},
		'float': { 
			'formatter': 'float_1', 
			'suffix': '', 
		},
		'string': { 
			'formatter': 'string', 
			'suffix': '', 
		},
		'temperature': { 
			'formatter': 'float_1', 
			'suffix': u'\u00B0C', 
		},
		'humidity': {
			'formatter': 'int',
			'suffix': '%',
		},
		'size': { 
			'formatter': 'int', 
			'suffix': 'MB', 
		},
		'percentage': { 
			'formatter': 'float_1', 
			'suffix': '%', 
		},
		'voltage': { 
			'formatter': 'float_2', 
			'suffix': 'v', 
		},
		'length': { 
			'formatter': 'float_1',
			'suffix': 'mm', 
		},
		'pressure': {
			'formatter': 'int',
			'suffix': 'mb',
		},
		'speed': {
			'formatter': 'float_1',
			'suffix': 'km/h',
		},
		'image': { 
			'formatter': "", 
			'suffix': "",
		},
		'calendar': {
			'formatter': "",
			'suffix': "",
		},
		'position': {
			'formatter': "",
			'suffix': "",
		},
                'duration': {
                        'formatter': 'int',
                        'suffix': 'h',
                }
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
				'title': ' ',
				'opposite': True,
				'plotLines': [],
			},
			'credits': { 
				'enabled': False,
			},
			'legend': {
				'enabled': True,
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
				'flags': {
					'useHTML' : True,
					'color': 'gray',
					'allowPointSelect': False,
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
				'dateTimeLabelFormats': {
					'day': '%A',
				},
			},
		},
		'chart_inverted': {
			'template': 'master',
			'chart': {
				'inverted': True,
			},
			'xAxis': {
				'type': 'datetime',
				'dateTimeLabelFormats': {
					'day': '%A',
				},
			},
		},
		'chart_short_inverted': {
			'template': 'master',
			'chart': {
				'height': 194,
				'inverted': True,
			},
			'xAxis': {
				'tickInterval': 24* 3600 * 1000,
				'tickWidth': 0,
				'gridLineWidth': 0,
				'type': 'datetime',
				'dateTimeLabelFormats': {
					'day': '%A',
				},
			},
		},
		'chart_sensor_group_summary': {
			'template': 'master',
			'chart': {
				'type': 'columnrange',
				'inverted': True,
			},
			'xAxis': {
				'type': 'datetime',
				'categories': [],
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
					'dataLabels': {
						'enabled': True,
					},
				},
			],
		},
		'chart_sensor_group_timeline_history': {
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
		'chart_sensor_group_timeline_short_history': {
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
		'chart_sensor_group_timeline_recent': {
			'template': 'master',
			'chart': {
				'type': 'spline',
				'zoomType': 'x',
			},
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
		'chart_sensor_group_timeline_realtime': {	
			'template': 'master',
			'chart': {
				'type': 'spline',
				'zoomType': 'x',
			},
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
# add UTC offset
is_dst = time.daylight and time.localtime().tm_isdst > 0
utc_offset = - (time.altzone if is_dst else time.timezone)
constants["utc_offset"] = int(utc_offset/3600)

# return all the configuration settings as an object
def get_constants():
	return constants
