import copy
import time
import json
import requests
import os
import sys

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)

# variables
debug = 0
module = 1
default_color = "#7cb5ec";
hostname = config["website"]
export_url = "https://export.highcharts.com/"
charts_directory = os.path.abspath(os.path.dirname(__file__))+"/charts";
extension = "png"
export_data = {"width": 500, "async" : False, "type": extension}
hour = 3600;
day = 24*hour;
if (config["debug"]): debug = 1

# main
def main():
	# delete all the old charts
	filelist = [ f for f in os.listdir(charts_directory) if f.endswith("."+extension) ]
	for f in filelist:
		os.remove(charts_directory+"/"+f)
	# load the charts
	load()
	
# default chart options
default_chart_options = {
	'chart': {},
	'title': {'text': ''},
	'yAxis': {'title': {'text': ' '}},
	'xAxis': {},
	'credits': { 'enabled': False},
	'tooltip': {'crosshairs': True,'shared': True,'valueSuffix': 'C'},
	'legend': {'enabled': False},
	'rangeSelector' : {'selected' : 0},
};

default_columnrange_options = {
	'type': 'columnrange',
	'colorByPoint': True, 
	'pointWidth': 10, 
	'pointPadding': 0, 
	'dataLabels': {'enabled': True, 'style': { 'fontSize': '13px'}}
}
	
default_spline_options = {
	'type' : 'spline', 
	'lineWidth': 3,
	'zIndex' : 1,
	'marker': { 'enabled': True, 'radius': 4, 'fillColor': 'white', 'lineWidth': 2,'lineColor': default_color },
	'dataLabels': {'enabled': True, 'y': 40, 'borderRadius': 5, 'backgroundColor': 'rgba(252, 255, 197, 0.7)', 'borderWidth': 1, 'borderColor': '#AAA'},
	'enableMouseTracking': True,
};
	
default_arearange_options =  {
	'type' : 'arearange', 
	'zIndex' : 0, 
	'color': default_color,
	'fillOpacity': 0.2,
	'lineWidth': 1,
	'linkedTo': 'Outside'
};
	
default_flags_options =  {
		'type' : 'flags', 
		'useHTML' : True, 
		'name': 'Weather',
		'onSeries': 'main',
};

# save the chart to disk
def save_to_file(filename,request):
	with open(charts_directory+'/'+filename+'.'+extension,'wb') as fd:
		for chunk in request.iter_content(1000):
			fd.write(chunk)
	
# create a columnrange chart
def load_columnrange_chart(sensor,features):
	y = []
	x = []
	# prepare data structure
	try:
		if ('Yesterday' in features):
			min = float(requests.get(hostname+'weather/'+sensor+'/temperature/day:min?start=-2&end=-2&range=1').json()[0][1])
			max = float(requests.get(hostname+'weather/'+sensor+'/temperature/day:max?start=-2&end=-2&range=1').json()[0][1])
			y.append([min,max]);
			x.append('Yesterday');
		if ('Today' in features):
			min = float(requests.get(hostname+'weather/'+sensor+'/temperature/day:min?start=-1&end=-1&range=1').json()[0][1])
			max = float(requests.get(hostname+'weather/'+sensor+'/temperature/day:max?start=-1&end=-1&range=1').json()[0][1])
			y.append([min,max]);
			x.append('Today');
		if ('Normal' in features):
			min = float(requests.get(hostname+'weather/almanac/normal/min?start=-1&end=-1&range=1').json()[0][1])
			max = float(requests.get(hostname+'weather/almanac/normal/max?start=-1&end=-1&range=1').json()[0][1])
			y.append([min,max]);
			x.append('Normal');
		if ('Record' in features):
			min = float(requests.get(hostname+'weather/almanac/record/min?start=-1&end=-1&range=1').json()[0][1])
			max = float(requests.get(hostname+'weather/almanac/record/max?start=-1&end=-1&range=1').json()[0][1])
			y.append([min,max]);
			x.append('Record');
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)
	# prepare the options
	options = copy.deepcopy(default_chart_options)
	options['tooltip']['enabled'] = False;
	options['chart']['height'] = 300;
	options['chart']['inverted'] = True;
	options['xAxis']['categories'] = x;
	options['series'] = [];
	options['series'].append(copy.deepcopy(default_columnrange_options));
	options['series'][0]['name'] = "Temperature";
	options['series'][0]['data'] = y;
	try:
		data = copy.deepcopy(export_data)
		data["options"] = json.dumps(options)
		r = requests.post(export_url, data=data)
		save_to_file('almanac_'+sensor,r)
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)

# create a timeline chart
def load_timeline_chart(filename,series,history):
	# prepare the options
	options = {}
	options = copy.deepcopy(default_chart_options)
	options['xAxis']['type'] = 'datetime';
	options['chart']['zoomType'] = 'x';
	if (not history):
		options['navigator'] = {'enabled' : False};
		options['rangeSelector'] = {'enabled' : False};
	options['series'] = series
	try:
		data = copy.deepcopy(export_data)
		data["options"] = json.dumps(options)
		data["constr"] = "StockChart"
		r = requests.post(export_url, data=data)
		save_to_file(filename,r)
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)

# load all the charts
def load():
	# generate the almanac charts
	load_columnrange_chart('outdoor',['Yesterday','Today','Normal','Record'])
	load_columnrange_chart('indoor',['Yesterday','Today'])
	
	try:
		recent_start = str(int(time.time())-24*hour);
		# outside temperature recent
		series = [];
		series.append(copy.deepcopy(default_spline_options));
		series[0]['name'] = "Outside";
		series[0]['id'] = "main";
		series[0]['data'] = requests.get(hostname+"weather/outdoor/temperature/hour?start="+recent_start).json()
		series.append(copy.deepcopy(default_arearange_options));
		series[1]['name'] = "Outside Min/Max";
		series[1]['data'] =  requests.get(hostname+"weather/outdoor/temperature/hour:range?start="+recent_start).json();
		series.append(copy.deepcopy(default_flags_options));
		condition = requests.get(hostname+"weather/outdoor/condition/hour?start="+recent_start).json();
		flags = [];
		for j in range(0,len(condition)):
			flags.append({'x': condition[j][0], 'shape': 'url(https://icons.wxug.com/i/c/k/)', 'title': '<img width="20" heigth="20" src="https://icons.wxug.com/i/c/k/'+condition[j][1]+'.gif">'});
		series[2]['data'] = flags
		load_timeline_chart('recent_outdoor',series,False)
		
		# inside temperature recent
		series = [];
		series.append(copy.deepcopy(default_spline_options));
		series[0]['name'] = "Inside";
		series[0]['lineColor'] = "#000000";
		series[0]['data'] = requests.get(hostname+"weather/indoor/temperature/hour?start="+recent_start).json()
		series.append(copy.deepcopy(default_arearange_options));
		series[1]['name'] = "Inside Min/Max";
		series[1]['data'] =  requests.get(hostname+"weather/indoor/temperature/hour:range?start="+recent_start).json();
		load_timeline_chart('recent_indoor',series,False)
		
		history_start = str(int(time.time())-30*day)
		# outside temperature history
		series = [];
		series.append(copy.deepcopy(default_spline_options));
		series[0]['name'] = "Outside";
		series[0]['id'] = "main";
		series[0]['data'] = requests.get(hostname+"weather/outdoor/temperature/day?start="+history_start).json()
		series.append(copy.deepcopy(default_arearange_options));
		series[1]['name'] = "outside Min/Max";
		series[1]['data'] =  requests.get(hostname+"weather/outdoor/temperature/day:range?start="+history_start).json();
		series.append(copy.deepcopy(default_flags_options));
		condition = requests.get(hostname+"weather/outdoor/condition/day?start="+history_start).json();
		flags = [];
		for j in range(0,len(condition)):
			flags.append({'x': condition[j][0], 'shape': 'url(https://icons.wxug.com/i/c/k/)', 'title': '<img width="20" heigth="20" src="https://icons.wxug.com/i/c/k/'+condition[j][1]+'.gif">'});
		series[2]['data'] = flags		
		series.append(copy.deepcopy(default_spline_options));
		series[3]['name'] = "Record Min";
		series[3]['color'] = "blue";
		series[3]['marker'] = {};
		series[3]['dataLabels'] = {};
		series[3]['dataLabels']['enabled'] = False;
		series[3]['dashStyle'] = "ShortDash";
		series[3]['lineWidth'] = 1;
		series[3]['linkedTo'] = ':previous'
		series[3]['data'] =  requests.get(hostname+"weather/almanac/record/min?start="+history_start).json();
		series.append(copy.deepcopy(default_spline_options));
		series[4]['name'] = "Record Max";
		series[4]['color'] = "red";
		series[4]['marker'] = {};
		series[4]['dataLabels'] = {};
		series[4]['dataLabels']['enabled'] = False;
		series[4]['dashStyle'] = "ShortDash";
		series[4]['lineWidth'] = 1;
		series[4]['linkedTo'] = ':previous'
		series[4]['data'] =  requests.get(hostname+"weather/almanac/record/max?start="+history_start).json();
		load_timeline_chart('history_outdoor',series,False)		

		# inside temperature history
		series = [];
		series.append(copy.deepcopy(default_spline_options));
		series[0]['name'] = "Inside";
		series[0]['lineColor'] = "#000000";
		series[0]['data'] = requests.get(hostname+"weather/indoor/temperature/day?start="+history_start).json()
		series.append(copy.deepcopy(default_arearange_options));
		series[1]['name'] = "Inside Min/Max";
		series[1]['data'] =  requests.get(hostname+"weather/indoor/temperature/day:range?start="+history_start).json();
		load_timeline_chart('history_indoor',series,False)
	
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)	

# main
if __name__ == '__main__':
	module=0
	main()
