#!/usr/bin/python
import sys
import os
import subprocess
import signal
import requests
import time
import math
import traceback
import datetime
import numpy
import random
import __builtin__
from math import radians, cos, sin, asin, sqrt
import Queue
import threading
import json

import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# remove all occurences of value from array
def remove_all(array,value_array):
	return [x for x in array if x not in value_array]

# return the current offset from utc time
def get_utc_offset():
	is_dst = time.daylight and time.localtime().tm_isdst > 0
	utc_offset = - (time.altzone if is_dst else time.timezone)
	return int(utc_offset/3600)

# return the timestamp with a the timezone offset applied
def timezone(timestamp):
	return int(timestamp+get_utc_offset()*conf["constants"]["1_hour"])

# return an UTC timestamp from a local timezone timestamp
def utc(timestamp):
	return int(timestamp-get_utc_offset()*conf["constants"]["1_hour"])

# return the now timestamp (in the local timezone)
def now():
	return timezone(int(time.time()))

# return yesterday's timestamp (in the local timezone)
def yesterday():
	return now()-24*conf["constants"]["1_hour"]

# return the last hour timestamp
def last_hour():
	return now()-60*conf["constants"]["1_minute"]

# generate a given timestamp based on the input (in the local timezone)
def get_timestamp(years,months,days,hours,minutes,seconds):
	timestamp = datetime.datetime(years,months,days,hours,minutes,seconds,0)
	return timezone(int(time.mktime(timestamp.timetuple())))

# return day start timestamp
def day_start(timestamp):
	date = datetime.datetime.fromtimestamp(utc(timestamp))
	return get_timestamp(date.year,date.month,date.day,0,0,0)

# return day end timestamp
def day_end(timestamp):
	date = datetime.datetime.fromtimestamp(utc(timestamp))
	return get_timestamp(date.year,date.month,date.day,23,59,59)

# return hour start timestamp
def hour_start(timestamp):
	date = datetime.datetime.fromtimestamp(utc(timestamp))
	return get_timestamp(date.year,date.month,date.day,date.hour,0,0)

# return hour end timestamp
def hour_end(timestamp):
	date = datetime.datetime.fromtimestamp(utc(timestamp))
	return get_timestamp(date.year,date.month,date.day,date.hour,59,59)

# return the realtime timestamp
def realtime(hours=conf["general"]["timeframes"]["realtime_hours"]):
	return now()-hours*conf["constants"]["1_hour"]

# return the recent timestamp
def recent(hours=conf["general"]["timeframes"]["recent_hours"]):
	return now()-hours*conf["constants"]["1_hour"]

# return the history timestamp
def history(days=conf["general"]["timeframes"]["history_days"]):
	return now()-days*conf["constants"]["1_day"]

# return a timestamp as a human readable format
def timestamp2date(timestamp):
	return datetime.datetime.fromtimestamp(utc(int(timestamp))).strftime('%Y-%m-%d %H:%M:%S')

# return the difference between two timestamps in a human readable format
def timestamp_difference(date1,date2):
	seconds = math.floor(math.fabs(date1-date2))
	interval = math.floor(seconds / 31536000)
	if interval > 1: return str(int(interval)) + " years ago"
	interval = math.floor(seconds / 2592000)
	if interval > 1: return str(int(interval)) + " months ago"
	interval = math.floor(seconds / 86400)
	if interval > 1: return str(int(interval)) + " days ago"
	interval = math.floor(seconds / 3600)
	if interval > 1: return str(int(interval)) + " hours ago"
	interval = math.floor(seconds / 60)
	if interval > 1: return str(int(interval)) + " minutes ago"
	return str(int(math.floor(seconds))) + " seconds ago"

# convert a string into a timestamp
def string2timestamp(string):
	if "s" in string: return now()-int(string.replace("s",""))
	elif "m" in string: return now()-int(string.replace("m",""))*60
	elif "h" in string: return now()-int(string.replace("d",""))*60*60
	elif "d" in string: return now()-int(string.replace("h",""))*60*60*24

# return true if the input is a number
def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False

# normalize the value. If the input is a number, keep a single digit, otherwise return a string
def normalize(value,formatter=None):
	if value == conf["constants"]["null"]: return conf["constants"]["null"]
	if formatter is None:
		return float("{0:.1f}".format(float(value))) if is_number(value) else str(value)
	elif formatter == "int": return int(float(value))
	elif formatter == "float_1": return float("{0:.1f}".format(float(value)))
	elif formatter == "float_2": return float("{0:.2f}".format(float(value)))
	else: return str(value)

# request a given url
def web_get(url,username=None,password=None,binary=False,params={},timeout=conf['constants']['web_timeout']):
	log.debug("Requesting web page "+url)
	if username is not None: request = requests.get(url,params=params,auth=(username,password),timeout=timeout,verify=False)
	else: request = requests.get(url,params=params,timeout=conf['constants']['web_timeout'],verify=False)
	if binary: return request.content
	else: return request.text

# calculate the min of a given array of data
def min(data):
	data = remove_all(data,[None,""])
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.min(data)
		else: return None
	else: return None

# calculate the max of a given array of data
def max(data):
	data = remove_all(data,[None,""])
	if len(data) > 0: 
		if is_number(data[0]): return __builtin__.max(data)
		else: return None
	else: return None

# calculate the velocity of change of a given array of data
def velocity(in_x,in_y):
	x = []
	y = []
	# if data is invalid, remove it from both the x and y arrays
	for i in range(len(in_y)):
		if in_y[i] is not None and in_y[i] != "None" and is_number(in_y[i]):
			x.append(in_x[i])
			y.append(in_y[i])
	# at least two values needed
	if len(y) >= 2:
		# normalize the x data to be in the range [0,1]
		min = x[0]
		max = x[len(x)-1]
		for i in range(0,len(x)): x[i] = float(x[i]-min)/float(max-min)
		# apply linear regression to interpolate the data
		z = numpy.polyfit(x,y,1)
		# return the coefficient
		return  normalize(z[0],"float_2")
	else: return None

# calculate the avg of a given array of data
def avg(data):
	data = remove_all(data,[None,""])
	if len(data) > 0:
		if is_number(data[0]): return normalize(numpy.mean(data))
		else: return __builtin__.max(set(data), key=data.count)
	else: return None

# calculate the sum of a given array of data
def sum(data):
        data = remove_all(data,[None,""])
        if len(data) > 0:
                if is_number(data[0]): return normalize(numpy.sum(data))
                else: return 0
        else: return 0

# count the items of a given array of data
def count(data):
        data = remove_all(data,[None,""])
	return len(data)

# count the (unique) items of a given array of data
def count_unique(data):
        data = remove_all(data,[None,""])
        return len(set(data))

# return the exception as a string
def get_exception(e):
	etype, value, tb = sys.exc_info()
	error = ''.join(traceback.format_exception(etype, value, tb,None))
	return error.replace('\n','|')

# return a random int between min and max
def randint(min,max):
	return random.randint(min,max)

# truncate a long string 
def truncate(string):
	max_len = 50
	return (string[:max_len] + '...') if len(string) > max_len else string

# return a dict merging delta into template
def merge(template,delta):
	new_dict = template.copy()
	new_dict.update(delta)

# return a given module
def get_module(module_id):
	for i in range(len(conf["modules"])):
		module = conf["modules"][i]
		if not module["enabled"]: continue
		if module["module_id"] == module_id: return module
	return None

# return the sensors belonging to the same group
def get_group(module_id,group_id):
	sensors = []
	for i in range(len(conf["modules"])):
		module = conf["modules"][i]
		if not module["enabled"]: continue
		if "sensors" not in module: continue
		for j in range(len(module["sensors"])):
			sensor = module["sensors"][j]
			if sensor["enabled"] and sensor["module_id"] == module_id and sensor["group_id"] == group_id: sensors.append(sensor)
	if len(sensors) == 0: return None
	return sensors

# return the sensors belonging to the same group
def get_group_string(group_string):
	split = group_string.split(":",2)
	if len(split) < 2: return None
	return get_group(split[0],split[1])

# fetch a sensor
def get_sensor(module_id,group_id,sensor_id):
	sensors = get_group(module_id,group_id)
	if sensors is None: return None
	for j in range (len(sensors)):
		sensor = sensors[j]
		if sensor["enabled"] and sensor["sensor_id"] == sensor_id: return sensor
	return None

# fetch a sensor
def get_sensor_string(sensor_string):
	split = sensor_string.split(":",3)
	if len(split) < 3: return None
	return get_sensor(split[0],split[1],split[2])

# helper class for running a command in a separate thread with a timeout
class Command(object):
	def __init__(self,cmd,shell,background):
		self.cmd = cmd
		self.process = None
		self.shell = shell
		self.background = background
	def run(self, timeout):
		def target(queue):
			# if running in a shell, the os.setsid() is passed in the argument preexec_fn so it's run after the fork() and before  exec() to run the shell
			preexec_fn = os.setsid if self.shell else None
			# run the process
			self.process = subprocess.Popen(self.cmd, shell=self.shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=preexec_fn)
			# if running in background, just return (and discard the output)
			if self.background: return
			# read the output line by line
			for line in iter(self.process.stdout.readline,''):
				# add the line to the queue
				queue.put_nowait(str(line))
		# a queue will be used to collect the output
		queue = Queue.Queue()
		# setup the thread
		thread = threading.Thread(target=target,args=[queue])
		# start the thread
		thread.start()
		# wait for it for timeout 
		thread.join(timeout)
		if thread.is_alive():
			# if the process is still alive, terminate it
			self.process.terminate()
			# if running in a shell send the signal to all the process groups
			if self.shell: os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
			thread.join()
		# return the output
		output = ""
		if queue.qsize() == 0: return output
		try:
			# merge the lines from the queue into a single string
			while True: output = output +str(queue.get_nowait())
		except: 
			# queue is empty, return the output
			return output.rstrip()

# run a command and return the output
def run_command(command,timeout=conf["constants"]["command_timeout"],shell=True,background=False):
	log.debug("Executing "+str(command))
	command = Command(command,shell,background)
	return command.run(timeout)

# determine if it is night
def is_night():
	is_night = False
	hour = int(time.strftime("%H"))
	if hour >= 20 or hour <= 6: is_night = True;
	return is_night

# convert the temperature if needed
def temperature_unit(temperature,force=False):
	if conf["general"]["units"]["fahrenheit"] or force: return "{0:.1f}".format(float(temperature * 1.8 + 32))
	else: return temperature

# convert a length if neeeded
def length_unit(length,force=False):
	if conf["general"]["units"]["imperial"] or force: return "{0:.1f}".format(float(length*0.039370))
	else: return length

# convert a pressure if neeeded
def pressure_unit(pressure,force=False):
	if conf["general"]["units"]["imperial"] or force: return "{0:.2f}".format(float((29.92 * pressure) / 1013.25))
	else: return pressure

# convert a speed if needed
def speed_unit(speed,force=False):
	if conf["general"]["units"]["imperial"] or force: return "{0:.1f}".format(float(speed*0.621371))
	else: return speed

# return the file path of a given widget id
def get_widget_file(widget_id):
	return conf['constants']['tmp_dir']+'/chart_'+widget_id+'.'+conf['constants']['chart_extension']

# return a widget
def get_widget(module_id,widget_id):
        module = get_module(module_id)
        if module is None: return
        if 'widgets' not in module: return
        for i in range(len(module["widgets"])):
                for j in range(len(module["widgets"][i])):
                        # for each widget
                        widget = module["widgets"][i][j]
			if not widget["enabled"]: continue
                        if widget_id == widget["widget_id"]: return widget

# return the distance in km between two coordinates
def distance(a,b):
	if len(a) != 2 or len(b) != 2: return 0
	lat1 = a[0]
	lon1 = a[1]
	lat2 = b[0]
	lon2 = b[1]
	# convert decimal degrees to radians 
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	km = 6367 * c
	return length_unit(km)

# check if a file exists on the filesystem
def file_exists(file):
	return os.path.isfile(file)

# return the text for the configured language
def lang(display_name):
	language = conf["general"]["language"]
	# return the text corresponding to the configured language
	if language in display_name: return display_name[language]
	log.warning("cannot find language "+language+" in "+str(display_name))
	return "N.A."

# convert a hex string into an integer
def hex2int(hex):
        try:
                hex = "0x"+hex.replace(" ","")
                return int(hex, 16)
        except: return None

# convert a hex string into a ascii string
def hex2string(hex):
        try:
                string = hex.decode("hex")
                return string
        except: return None

# for a location parse the json data and return the label
def parse_position(data,key):
        if len(data) != 1: return []
        data = json.loads(data[0])
        return [data[key]]

# for a calendar parse the json data and return the value
def parse_calendar(data):
        # the calendar string is at position 0
        if len(data) != 1: return []
        data = json.loads(data[0])
        # the list of events is at position 1
        if len(data) != 2: return []
        events = json.loads(data[1])
        for event in events:
                # generate the timestamp of start and end date
                start_date = datetime.datetime.strptime(event["start_date"],"%Y-%m-%dT%H:%M:%S.000Z")
                start_timestamp = timezone(timezone(int(time.mktime(start_date.timetuple()))))
                end_date = datetime.datetime.strptime(event["end_date"],"%Y-%m-%dT%H:%M:%S.000Z")
                end_timestamp = timezone(timezone(int(time.mktime(end_date.timetuple()))))
                now_ts = now()
                # check if we are within an event
                if now_ts > start_timestamp and now_ts < end_timestamp: return [event["text"]]
        return [""]

# return true if running on raspberry pi
def is_raspberry():
        with open("/proc/cpuinfo",'r') as file:
                cpu = file.read()
        file.close()
        if "BCM" in cpu: return True
        return False

