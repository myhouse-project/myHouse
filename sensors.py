#!/usr/bin/python
import sys
import os
import datetime
import json
import base64
import time
import copy

import utils
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()

import plugin_wunderground
import plugin_weatherchannel
import plugin_linux
import plugin_image
import plugin_csv
import plugin_messagebridge
import plugin_icloud
import plugin_rtl_433
import plugin_gpio

# variables
plugins = {}

# initialize the configured plugins
def init_plugins(start_services):
        # for each plugin
        for name in conf["plugins"]:
                # get the plugin and store it
	        plugin = None
	        if name == "wunderground": plugin = plugin_wunderground
	        elif name == "weatherchannel": plugin = plugin_weatherchannel
	        elif name == "linux": plugin = plugin_linux
	        elif name == "image": plugin = plugin_image
		elif name == "icloud": plugin = plugin_icloud
	        elif name == "csv": plugin = plugin_csv
	        elif name == "messagebridge": plugin = plugin_messagebridge
		elif name == "rtl_433": plugin = plugin_rtl_433
		elif name == "gpio": plugin = plugin_gpio
                if plugin is None:
                        log.error("plugin "+name+" not supported")
                        continue
                plugins[name] = plugin
                # start the plugin service
		if hasattr(plugin, 'run') and start_services:
	                log.info("starting plugin service "+name)
	                schedule.add_job(plugin.run,'date',run_date=datetime.datetime.now())

# read data out of a sensor and store the output in the cache
def poll(sensor):
	# poll the data
	data = None
	log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] polling sensor")
        try: 
		# retrieve the raw data 
		data = plugins[sensor['plugin']['plugin_name']].poll(sensor)
                # delete from the cache the previous value
                db.delete(sensor['db_cache'])
	        # store it in the cache
	        db.set(sensor["db_cache"],data,utils.now())
	except Exception,e: 
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to poll: "+utils.get_exception(e))
	return data

# parse the data of a sensor from the cache and return the value read
def parse(sensor):
	# retrieve the raw data from the cache
	data = db.range(sensor["db_cache"],withscores=False)
	if len(data) == 0: 
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"]: no data to parse")
		return None
	data = data[0]
	measures = None
        try:
		# parse the cached data
		measures = plugins[sensor['plugin']['plugin_name']].parse(sensor,data)
		# format each values
		for i in range(len(measures)): 
			# normalize the measures
			if sensor["format"] == "temperature": measures[i]["value"] = utils.temperature_unit(measures[i]["value"])
			if sensor["format"] == "length": measures[i]["value"] = utils.length_unit(measures[i]["value"])
			if sensor["format"] == "pressure": measures[i]["value"] = utils.pressure_unit(measures[i]["value"])
			if sensor["format"] == "speed": measures[i]["value"] = utils.speed_unit(measures[i]["value"])
			measures[i]["value"] = utils.normalize(measures[i]["value"],conf["constants"]["formats"][sensor["format"]]["formatter"])
		log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] parsed: "+str(measures))
	except Exception,e:
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to parse "+str(data)+": "+utils.get_exception(e))
	# return the structured data
	return measures

# save the data of a sensor into the database
def save(sensor,force=False):
	cache_timestamp = 0
	# get the raw data from the cache
	if db.exists(sensor["db_cache"]):
		data = db.range(sensor["db_cache"],withscores=True)
		cache_timestamp = data[0][0]
	# if too old, refresh it
	cache_expire_min = sensor["plugin"]["cache_expire_min"] if "plugin" in sensor and "cache_expire_min" in sensor["plugin"] else conf["sensors"]["cache_expire_min"]
	if force or (utils.now() - cache_timestamp) > cache_expire_min*conf["constants"]["1_minute"]:
		# if an exception occurred, skip this sensor
		if poll(sensor) is None: return
	# get the parsed data
	measures = parse(sensor)
	# store it into the database
	store(sensor,measures)

# store the measures into the database
def store(sensor,measures):
	# if an exception occurred, skip this sensor
	if measures is None: return
	# for each returned measure
	for measure in measures:
	        # set the timestamp to now if not already set
	        if "timestamp" not in measure: measure["timestamp"] = utils.now()
		# define the key to store the value
		key = sensor["db_group"]+":"+measure["key"]
		# delete previous values if needed
		if "single_instance" in sensor and sensor["single_instance"]: db.delete(key)
		# check if there is already a value stored with the same timestamp
		old = db.rangebyscore(key,measure["timestamp"],measure["timestamp"])
		if len(old) > 0:
			# same value and same timestamp, do not store
			log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") ignoring "+measure["key"]+": "+str(measure["value"]))
			continue
		# apply the bias of the sensor if configured
		if "bias" in sensor: measure["value"] = measure["value"]+sensor["bias"]
		# store the value into the database
		log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") saving "+measure["key"]+": "+utils.truncate(str(measure["value"]))+conf["constants"]["formats"][sensor["format"]]["suffix"])
		db.set(key,measure["value"],measure["timestamp"])
		# re-calculate the avg/min/max of the hour/day
		if "summarize" in sensor:
			summarize(sensor,'hour',utils.hour_start(measure["timestamp"]),utils.hour_end(measure["timestamp"]))
	                summarize(sensor,'day',utils.day_start(measure["timestamp"]),utils.day_end(measure["timestamp"]))

# calculate min, max and avg value
def summarize(sensor,timeframe,start,end):
	# prepare the database schema to use
	if timeframe == "hour": 
		key_to_read = sensor["db_sensor"]
		key_to_write = sensor["db_sensor"]+":hour"
	elif timeframe == "day":
                key_to_read = sensor["db_sensor"]+":hour:avg"
                key_to_write = sensor["db_sensor"]+":day"
	# retrieve from the database the data based on the given timeframe
	data = db.rangebyscore(key_to_read,start,end,withscores=False)
	timestamp = start
	min = avg = max = "-"
	if sensor["summarize"]["avg"]:
		# calculate avg
		avg = utils.avg(data)
		db.deletebyscore(key_to_write+":avg",start,end)
       		db.set(key_to_write+":avg",avg,timestamp)
	if sensor["summarize"]["min_max"]:
		# calculate min
		min = utils.min(data)
		db.deletebyscore(key_to_write+":min",start,end)
                db.set(key_to_write+":min",min,timestamp)
		# calculate max
		max = utils.max(data)
		db.deletebyscore(key_to_write+":max",start,end)
                db.set(key_to_write+":max",max,timestamp)
	log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(timestamp)+") updating summary of the "+timeframe+" (min,avg,max): ("+str(min)+","+str(avg)+","+str(max)+")")

# purge old data from the database
def expire(sensor):
	total = 0
	for stat in ["",':hour:min',':hour:avg',':hour:max']:
		key = sensor['db_sensor']+stat
		if db.exists(key):
			deleted = db.deletebyscore(key,"-inf",utils.now()-conf["sensors"]["data_expire_days"]*conf["constants"]["1_day"])
			log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expiring from "+stat+" "+str(total)+" items")
			total = total + deleted
	log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expired "+str(total)+" items")

# initialize a sensor data structure
def init_sensor(sensor,module_id):
	# initialize a new data structure
	sensor = copy.deepcopy(sensor)
        sensor['module_id'] = module_id
        # define the database schema
        sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module_id"]+":"+sensor["group_id"]
        sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
	if "plugin" in sensor:
		# ensure the sensor is using a valid plugin
	        if sensor["plugin"]["plugin_name"] not in plugins:
	                log.error("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] plugin "+sensor["plugin"]["plugin_name"]+" not supported")
	                return None
	        # define the cache location if cache is in use by the plugin
		if hasattr(plugins[sensor["plugin"]["plugin_name"]], 'cache_schema'):
	                if plugins[sensor["plugin"]["plugin_name"]].cache_schema(sensor) is None:
	                        log.error("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] invalid measure")
	                        return None
	                sensor['db_cache'] = conf["constants"]["db_schema"]["root"]+":"+conf["constants"]["db_schema"]["tmp"]+":plugin_"+sensor["plugin"]["plugin_name"]+":"+plugins[sensor["plugin"]["plugin_name"]].cache_schema(sensor)
	return sensor

# read or save the measure of a given sensor
def run(module_id,group_id,sensor_id,action):
	# ensure the group and sensor exist
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
	sensor = init_sensor(sensor,module_id)
	if sensor is None: 
		log.error("["+module_id+"]["+group_id+"]["+sensor_id+"] not found, skipping it")
		return
	# execute the action
	log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] requested "+action)
	if action == "poll":
		# read the measure (will be stored into the cache)
		poll(sensor)
	elif action == "parse":
		# just parse the output
		log.info(parse(sensor))
	elif action == "save":
		# save the parsed output into the database
		save(sensor)
        elif action == "force_save":
                # save the parsed output into the database forcing polling the measure
                save(sensor,force=True)
	elif action == "summarize_hour": 
		# every hour calculate and save min,max,avg of the previous hour
		summarize(sensor,'hour',utils.hour_start(utils.last_hour()),utils.hour_end(utils.last_hour()))
        elif action == "summarize_day":
		# every day calculate and save min,max,avg of the previous day (using hourly averages)
                summarize(sensor,'day',utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()))
	elif action == "expire":
		# purge old data from the database
		expire(sensor)
	else: log.error("Unknown action "+action)

# schedule all the sensors
def schedule_all():
	# init plugins
	init_plugins(True)
	log.info("setting up all the configured sensors")
        # for each module
        for module in conf["modules"]:
		if not module["enabled"]: continue
		# skip group without sensors
		if "sensors" not in module: continue
		for sensor in module["sensors"]:
			# initialize the sensor data structure
			sensor = init_sensor(sensor,module['module_id'])
			if sensor is None: continue
			# skip sensors without a plugin
			if 'plugin' not in sensor: continue
			# the plugin needs sensors to be registered with it first
			if hasattr(plugins[sensor['plugin']['plugin_name']],'register'):
				# register the sensor
				log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] registering with plugin service "+sensor['plugin']['plugin_name'])
				plugins[sensor['plugin']['plugin_name']].register(sensor)
			# the plugin needs the sensor to be polled
			if "polling_interval" in sensor["plugin"]:
				# schedule polling
				log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling polling every "+str(sensor["plugin"]["polling_interval"])+" minutes")
				# run it now first
				if conf["sensors"]["poll_at_startup"]: schedule.add_job(run,'date',run_date=datetime.datetime.now()+datetime.timedelta(seconds=utils.randint(1,59)),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'save'])
                                # then schedule it for each refresh interval
       	                        schedule.add_job(run,'cron',minute="*/"+str(sensor["plugin"]["polling_interval"]),second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'save'])
                        # schedule an expire job every day
                        schedule.add_job(run,'cron',hour="1",minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'expire'])
			# schedule a summarize job every hour and every day if needed
                        if "summarize" in sensor:
              	        	log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling summary every hour and day")
                     	        schedule.add_job(run,'cron',minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'summarize_hour'])
                             	schedule.add_job(run,'cron',hour="0",minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'summarize_day'])

# return the latest read of a sensor for a web request
def data_get_current(module_id,group_id,sensor_id):
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
	if "plugin" in sensor and "poll_on_demand" in sensor["plugin"] and sensor["plugin"]["poll_on_demand"]:
		# the sensor needs to be polled on demand
		run(module_id,group_id,sensor_id,"save")
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":"+group_id+":"+sensor_id
        # return the latest measure
        data = db.range(key,withscores=False,milliseconds=True,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
	# if an image, decode it and return it
	if sensor["format"] == "image": return base64.b64decode(data[0])
	else: return json.dumps(data)

# return the latest image of a sensor for a web request
def data_get_current_image(module_id,group_id,sensor_id,night_day):
	data = json.loads(data_get_current(module_id,group_id,sensor_id))
	if len(data) == 0: return ""
	filename = str(data[0])
	if night_day and utils.is_night(): filename = "nt_"+filename
	with open(conf["constants"]["web_dir"]+"/images/"+sensor_id+"_"+str(filename)+".png",'r') as file:
                data = file.read()
        file.close()
	return data

# return the time difference between now and the latest measure
def data_get_current_timestamp(module_id,group_id,sensor_id):
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":"+group_id+":"+sensor_id
	data = db.range(key,withscores=True,milliseconds=True)
	if len(data) > 0: return json.dumps([utils.timestamp_difference(utils.now(),data[0][0]/1000)])
	else: return json.dumps(data)

# return the data of a requested sensor based on the timeframe and stat requested
def data_get_data(module_id,group_id,sensor_id,timeframe,stat):
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
        if "plugin" in sensor and "poll_on_demand" in sensor["plugin"] and sensor["plugin"]["poll_on_demand"] and timeframe == "realtime":
                # the sensor needs to be polled on demand
                run(module_id,group_id,sensor_id,"save")
        data = []
        # get the parameters for the requested timeframe
        if timeframe == "realtime":
                # recent hourly measures up to now
                range = ""
                start = utils.realtime()
                end = utils.now()
                withscores = True
        elif timeframe == "recent":
                # recent hourly measures up to now
                range = ":hour"
                start = utils.recent()
                end = utils.now()
                withscores = True
        elif timeframe == "history":
                # historical daily measures up to new
                range = ":day"
                start = utils.history()
                end = utils.now()
                withscores = True
        elif timeframe == "short_history":
                # historical daily measures up to new
                range = ":day"
                start = utils.history(conf["timeframes"]["short_history_days"])
                end = utils.now()
                withscores = True
        elif timeframe == "today":
                # today's measure
                range = ":day"
                start = utils.day_start(utils.now())
                end = utils.day_end(utils.now())
                withscores = False
        elif timeframe == "yesterday":
                # yesterday's measure
                range = ":day"
                start = utils.day_start(utils.yesterday())
                end = utils.day_end(utils.yesterday())
                withscores = False
	elif timeframe == "forecast":
		# next days measures
                range = ":day"
                start = utils.day_start(utils.now())
                end = utils.day_start(utils.now()+(conf["timeframes"]["forecast_days"]-1)*conf["constants"]["1_day"])
                withscores = True
        else: return data
        # define the key to request
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":"+group_id+":"+sensor_id+range
        requested_stat = ":"+stat
        # if a range is requested, start asking for the min
        if stat == "range": requested_stat = ":min"
	if timeframe == "realtime": requested_stat = ""
        # request the data
        data = db.rangebyscore(key+requested_stat,start,end,withscores=withscores,milliseconds=True,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
        if stat == "range" and len(data) > 0:
                # if a range is requested, ask for the max and combine the results
                data_max = db.rangebyscore(key+":max",start,end,withscores=False,milliseconds=True,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
                for i, item in enumerate(data):
                        # ensure data_max has a correspondent value
                        if i < len(data_max):
                                if (isinstance(item,list)): data[i].append(data_max[i])
                                else: data.append(data_max[i])
        return json.dumps(data)

# set a sensor value
def data_set(module_id,group_id,sensor_id,value):
	log.debug("["+module_id+"]["+group_id+"]["+sensor_id+"] value to store: "+str(value))
        # ensure the group and sensor exist
        sensor = utils.get_sensor(module_id,group_id,sensor_id)
        sensor = init_sensor(sensor,module_id)
        if sensor is None:
                log.error("["+module_id+"]["+group_id+"]["+sensor_id+"] not found")
                return json.dumps("KO")
	# prepare the measure
	measures = []
	measure = {}
	measure["key"] = sensor["sensor_id"]
	measure["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
	measures.append(measure)
	# store it
	store(sensor,measures)
        return json.dumps("OK")

# send a message to a sensor
def data_send(module_id,group_id,sensor_id,value,force=False):
	log.debug("["+module_id+"]["+group_id+"]["+sensor_id+"] sending message: "+str(value))
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
        if sensor is None:
	        log.error("["+module_id+"]["+group_id+"]["+sensor_id+"] not found")
		return json.dumps("KO")
	if not hasattr(plugins[sensor["plugin"]["plugin_name"]], 'send'):
		log.error("the plugin "+sensor["plugin"]["plugin_name"]+" does not allow sending messages")
		return json.dumps("KO")
	plugins[sensor["plugin"]["plugin_name"]].send(sensor,value,force=force)
	return json.dumps("OK")

# allow running it both as a module and when called directly
if __name__ == '__main__':
	if len(sys.argv) != 5: 
		# no arguments provided, schedule all sensors
		schedule.start()
		schedule_all()
	        while True:
	                time.sleep(1)
	else: 
		# run the command for the given sensor
		# <module_id> <group_id> <sensor_id> <action>
		init_plugins(False)
		sensor = utils.get_sensor(sys.argv[1],sys.argv[2],sys.argv[3])
		if sensor is None: 
			log.info("invalid sensor provided")
		else: run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

