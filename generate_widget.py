#!/usr/bin/python
import copy
import json
import requests
import sys
from motionless import LatLonMarker,DecoratedMap

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

hostname = 'http://127.0.0.1:'+str(conf['gui']['port'])+'/'
export_url = 'https://export.highcharts.com/'
export_data = {"width": 500, "type": conf['constants']['chart_extension']}
debug = False

# debug http requests
if debug:
	try:
		import http.client as http_client
	except ImportError:
		# Python 2
		import httplib as http_client
	http_client.HTTPConnection.debuglevel = 1

# capitalize the first letter
def capitalizeFirst(string):
	return string.capitalize()

# return an image not available picture
def get_image_unavailable():
	with open(conf["constants"]["image_unavailable"],'r') as file:
		data = base64.b64encode(file.read())
	file.close()
	return data

# save the image to disk
def save_to_file(r,filename):
	with open(utils.get_widget_file(filename),'wb') as file:
		for chunk in r.iter_content(1000):
			file.write(chunk)
	file.close()

# generate the chart
def generate_chart(options,filename,is_stock_chart=False):
	data = copy.deepcopy(export_data)
	data["options"] = json.dumps(options)
	if is_stock_chart: data["constr"] = "StockChart"
	r = requests.post(export_url, data=data)
	save_to_file(r,filename)

# apply the format to the value
def apply_format(series,format):
	if 'tooltip' not in series: series['tooltip'] = {} 
	if 'dataLabels' not in series: series['dataLabels'] = {}
	series['tooltip']['valueSuffix'] = conf['constants']['formats'][format]['suffix'];
	series['dataLabels']['format'] = '{y}'+conf['constants']['formats'][format]['suffix'];

# add a new point to an existing series
def add_point(chart,url,series_index,category_index):
	data = json.loads(utils.web_get(hostname+url))
	# add the category index to the data
	if len(data) < 2: return
	data = [category_index,data[0],data[1]]	
	if 'data' not in chart['series'][series_index]: chart['series'][series_index]['data'] = []
	chart['series'][series_index]['data'].append(data)

# add a new series to a chart
def add_series(chart,url,sensor,series_index):
	data = json.loads(utils.web_get(hostname+url))
	# get the series template
	series = copy.deepcopy(sensor['series'][series_index])
	null_value = None
	if "null_value" in series: null_value = series["null_value"]
	# set the name and the id
	series['name'] = utils.lang(sensor['display_name'])+" "+sensor['series'][series_index]['series_id']
	series['id'] = sensor['sensor_id']+":"+sensor['series'][series_index]['series_id']
	# add the sensor suffix and tooltip
	apply_format(series,sensor['format'])
	# add the data to it
	series['data'] = data
	# if the data is a string, add flags
	if "type" in sensor['series'][series_index] and sensor['series'][series_index]['type'] == "flags":
		flags = []
		for i in range(len(data)):
			if data[i][1] == null_value or data[i][1] == None or data[i][1] == "": continue
#			flags.append({'x': int(data[i][0]), 'shape': 'url(https://icons.wxug.com/i/c/k/'+str(data[i][1])+'.gif)', 'title': '<img width="'+str(series['width'])+'" heigth="'+str(series['heigth'])+'" src="https://icons.wxug.com/i/c/k/'+str(data[i][1])+'.gif">'})
			flags.append({'x': int(data[i][0]), 'shape': 'circlepin', 'title': str(data[i][1])})
			series['data'] = flags
	# attach the series to the chart
	if 'series' not in chart: chart['series'] = []
	chart['series'].append(series)

# add a sensor summary widget
def add_sensor_group_summary_chart(layout,widget):
	if "group" in layout:
		sensors = utils.get_group_string(layout["group"])
		if sensors is None: return
	elif "sensors" in layout:
		sensors = []
		for i in range(len(layout["sensors"])):
			sensor_string = layout["sensors"][i]
			sensor = utils.get_sensor_string(sensor_string)
			if sensor is not None: sensors.append(sensor)
		if len(sensors) == 0: return
	else: return
	chart = copy.deepcopy(conf["constants"]["charts"]["chart_sensor_group_summary"])
	for i in range(len(sensors)):
		sensor = sensors[i];
		sensor_url = sensor["module_id"]+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
		if "exclude" in layout and sensor_url.replace("/",":") in layout["exclude"]: continue
		# skip flags
		if sensor['format'] == 'string': continue
		is_flag = False
		if "series" in sensor:
			for j in range(len(sensor["series"])):
				if "type" in sensor["series"][j] and sensor["series"][j]["type"] == "flags": is_flag = True
			if is_flag: continue
		# add the sensor to the xAxis
		chart['xAxis']['categories'].append(utils.lang(sensor["display_name"]))
		# apply the suffix to the today's series
		chart["series"][1]["dataLabels"]["format"] = '{y}'+conf['constants']['formats'][sensor["format"]]['suffix']
		# add the point for yesterday's range
		add_point(chart,sensor_url+"/yesterday/range",0,i);
		# add the point for today's range
		add_point(chart,sensor_url+"/today/range",1,i);
	chart['title']['text'] = utils.lang(widget["display_name"])
	generate_chart(chart,widget["widget_id"])

# add a sensor timeline widget
def add_sensor_group_timeline_chart(layout,widget):
	if "group" in layout:
		sensors = utils.get_group_string(layout["group"])
		if sensors is None: return
	elif "sensors" in layout:
		sensors = []
		for i in range(len(layout["sensors"])):
			sensor_string = layout["sensors"][i]
			sensor = utils.get_sensor_string(sensor_string)
			if sensor is not None: sensors.append(sensor)
		if len(sensors) == 0: return
	else: return
	chart = copy.deepcopy(conf["constants"]["charts"]["chart_"+layout["type"]+"_"+layout["timeframe"]])
	# for each sensor
	for i in range(len(sensors)):
		sensor = sensors[i]
		sensor_url = sensor["module_id"]+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
		if "series" not in sensor: continue
		# add each series, to the chart
		for j in range(len(sensor["series"])):
			series = sensor["series"][j]
			if "exclude" in layout and (sensor_url.replace("/",":") in layout["exclude"] or sensor_url.replace("/",":")+","+series["series_id"] in layout["exclude"]): continue
			# ignore range series for realtime charts
			if layout["timeframe"] == "realtime" and series["series_id"] == "range": continue
			# reduce the history timeframe for email notifications
			timeframe = "short_history" if layout["timeframe"] == "history" else layout["timeframe"]
			# add the series to the chart
			add_series(chart,sensor_url+"/"+timeframe+"/"+series["series_id"],sensor,j)
	chart['title']['text'] = utils.lang(widget["display_name"])
	generate_chart(chart,widget["widget_id"])

# add a generic sensor chart widget
def add_sensor_chart(layout,widget):
	if "sensor" not in layout: return
	sensor = utils.get_sensor_string(layout["sensor"])
	if sensor is None: return
	sensor_url = sensor["module_id"]+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
	chart = copy.deepcopy(conf["constants"]["charts"][layout["type"]])
	if sensor["format"] == "percentage": chart["yAxis"]["max"] = 100
	# add each series to the chart
	if "series" not in sensor: return
	for i in range(len(sensor["series"])):
		series = sensor["series"][i]
		if "exclude" in layout and (sensor_url.replace("/",":") in layout["exclude"] or sensor_url.replace("/",":")+","+series["series_id"] in layout["exclude"]): continue
		# reduce the history timeframe for email notifications
		timeframe = "short_history" if layout["timeframe"] == "history" else layout["timeframe"]
		add_series(chart,sensor_url+"/"+timeframe+"/"+series["series_id"],sensor,i)
	chart['title']['text'] = utils.lang(widget["display_name"])
	generate_chart(chart,widget["widget_id"])

# add an image widget
def add_sensor_image(layout,widget):
	if "sensor" not in layout: return
	sensor = utils.get_sensor_string(layout["sensor"])
	if sensor is None: return
	sensor_url = sensor["module_id"]+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
	r = requests.get(hostname+sensor_url+"/current")
	save_to_file(r,widget["widget_id"])

# add a map widget
def add_sensor_map(layout,widget):
	if "group" not in layout: return
	sensors = utils.get_group_string(layout["group"])
	if sensors is None: return
	# setup the map
	map = DecoratedMap(maptype=conf["gui"]["maps"]["type"],size_x=conf["gui"]["maps"]["size_x"],size_y=conf["gui"]["maps"]["size_y"])
	for i in range(len(sensors)):
		# for each sensor of the group
		sensor = sensors[i];
		sensor_url = sensor["module_id"]+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
		# retrieve the data
		markers = json.loads(utils.web_get(hostname+sensor_url+"/"+layout["timeframe"]+"/avg"))
		if len(markers) == 0: continue
		marker = json.loads(markers[len(markers)-1][1])
		# add the marker to the map
		map.add_marker(LatLonMarker(marker["latitude"],marker["longitude"], label=marker["label"][0].upper()))
	# download the map
	url = map.generate_url()
	r = requests.get(url,verify=False)
	save_to_file(r,widget["widget_id"])

# load all the widgets of the given module
def run(module_id,requested_widget=None,generate_widget=True):
	module = utils.get_module(module_id)
	widgets = []
	if module is None: return
	if 'widgets' not in module: return
	for i in range(len(module["widgets"])):
		for j in range(len(module["widgets"][i])):
			# for each widget
			widget = module["widgets"][i][j]
			if requested_widget is not None and widget["widget_id"] != requested_widget: continue
			if not widget["enabled"]: continue
			# generate the widget
			if "layout" not in widget: continue
			for k in range(len(widget["layout"])):
				layout = widget["layout"][k]
				chart_generated = True
				if layout["type"] == "sensor_group_summary": 
					if generate_widget: add_sensor_group_summary_chart(layout,widget)
					break
				elif layout["type"] == "image": 
					if generate_widget: add_sensor_image(layout,widget)
					break
				elif layout["type"] == "sensor_group_timeline": 
					if generate_widget: add_sensor_group_timeline_chart(layout,widget)
					break
				elif layout["type"] == "chart_short" or layout["type"] == "chart_short_inverted": 
					if generate_widget: add_sensor_chart(layout,widget)
					break
				elif layout["type"] == "map":
					if generate_widget: add_sensor_map(layout,widget)
					break
				else: 
					chart_generated = False
					continue
			if chart_generated: widgets.append(widget["widget_id"])
	return widgets

# main
if __name__ == '__main__':
	if len(sys.argv) == 2: run(sys.argv[1])
	elif len(sys.argv) == 3: run(sys.argv[1],sys.argv[2])
	else: print "Usage: "+__file__+" <module_id> [widget_id]"
