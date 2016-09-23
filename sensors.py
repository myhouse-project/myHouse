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
import plugin_http
import plugin_messagebridge_pull
import plugin_messagebridge_push

# variables
push_plugins = {}

# return the appropriate plugin
def get_plugin(name):
	plugin = None
        if name == "wunderground": plugin = plugin_wunderground
        elif name == "weatherchannel": plugin = plugin_weatherchannel
        elif name == "linux": plugin = plugin_linux
        elif name == "http": plugin = plugin_http
        elif name == "messagebridge_pull": plugin = plugin_messagebridge_pull
	elif name == "messagebridge_push": plugin = plugin_messagebridge_push
	return plugin

# read data out of a sensor and store the output in the cache
def poll(sensor):
	# poll the data
	data = None
	log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] polling sensor")
        try: 
		# retrieve the raw data 
		data = sensor["plugin_module"].poll(sensor)
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
	data = db.range(sensor["db_cache"],withscores=False)[0]
	measures = None
        try:
		# parse the cached data
		measures = sensor["plugin_module"].parse(sensor,data)
		# format each values
		for i in range(len(measures)): 
			# normalize the measures
			if sensor["format"] == "temperature": measures[i]["value"] = utils.temperature_unit(measures[i]["value"])
			if sensor["format"] == "length": measures[i]["value"] = utils.length_unit(measures[i]["value"])
			measures[i]["value"] = utils.normalize(measures[i]["value"],conf["constants"]["formats"][sensor["format"]]["formatter"])
		log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] parsed: "+str(measures))
	except Exception,e:
		log.warning("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to parse "+str(data)+": "+utils.get_exception(e))
	# return the structured data
	return measures

# save the data of a sensor into the database
def save(sensor):
	cache_timestamp = 0
	# get the raw data from the cache
	if db.exists(sensor["db_cache"]):
		data = db.range(sensor["db_cache"],withscores=True)
		cache_timestamp = data[0][0]
	# if too old, refresh it
	if utils.now() - cache_timestamp > conf['constants']['cache_expire_min']*conf["constants"]["1_minute"]:
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
		if sensor["format"] == "image": db.delete(key)
		# check if there is already a alue stored at the same timestamp
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
		if sensor["calculate_avg"]:
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
	if sensor["calculate_avg"]:
		# calculate avg
		avg = utils.avg(data)
		db.deletebyscore(key_to_write+":avg",start,end)
       		db.set(key_to_write+":avg",avg,timestamp)
	if sensor["calculate_min_max"]:
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
			deleted = db.deletebyscore(key,"-inf",utils.now()-conf["constants"]["data_expire_days"]*conf["constants"]["1_day"])
			log.debug("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expiring from "+stat+" "+str(total)+" items")
			total = total + deleted
	log.info("["+sensor["module_id"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expired "+str(total)+" items")

# initialize a sensor data structure
def init_sensor(sensor,module_id,group_id):
	sensor = copy.deepcopy(sensor)
        # add group and module if not there yet
        sensor['module_id'] = module_id
        sensor['group_id'] = group_id
        # determine the plugin to use
        sensor["plugin_module"] = get_plugin(sensor["plugin"]["name"])
        if sensor["plugin_module"] is None:
                log.error("["+module_id+"]["+group_id+"]["+sensor_id+"] plugin "+sensor["plugin"]["name"]+" not supported")
                return None
        # define the database schema
        sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module_id"]+":sensors:"+sensor["group_id"]
        sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
        # define the cache location if cache is in use by the plugin
	if hasattr(sensor["plugin_module"], 'cache_schema'):
                if sensor["plugin_module"].cache_schema(sensor) is None:
                        log.error("["+module_id+"]["+group_id+"]["+sensor_id+"] invalid request")
                        return None
                sensor['db_cache'] = conf["constants"]["db_schema"]["root"]+":tmp:plugin_"+sensor["plugin"]["name"]+":"+sensor["plugin_module"].cache_schema(sensor)
	return sensor

# read or save the measure of a given sensor
def run(module_id,group_id,sensor_id,action):
	# ensure the group and sensor exist
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
	sensor = init_sensor(sensor,module_id,group_id)
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
		parse(sensor)
	elif action == "save":
		# save the parsed output into the database
		save(sensor)
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

# initialize configured push plugins
def init_push_plugins():
        # for each push plugin
        for plugin_name,plugin_conf in conf["plugins"].iteritems():
                # skip pull plugins
                if plugin_conf["type"] != "push": continue
                # get the plugin and store it
                plugin_module = get_plugin(plugin_name)
                if plugin_module is None:
                        log.error("push plugin "+plugin_name+" not supported")
                        continue
                push_plugins[plugin_name] = plugin_module
                # start the plugin
                log.info("starting push plugin "+plugin_name)
		schedule.add_job(plugin_module.run,'date',run_date=datetime.datetime.now())

# schedule each sensor
def schedule_all():
	# init push plugins
	init_push_plugins()
	log.info("scheduling polling for every configured sensor")
        # for each module
        for module in conf["modules"]:
		if not module["enabled"]: continue
		# skip modules without sensor groups
		if "sensor_groups" not in module: continue
	        # for each group of sensors
                for group in module["sensor_groups"]:
			# skip group without sensors
			if "sensors" not in group: continue
			for sensor in group["sensors"]:
				# initialize the sensor
				sensor = init_sensor(sensor,module['module_id'],group['group_id'])
				if sensor is None: continue
				# skip sensors wihtout a plugin
				if 'plugin' not in sensor: continue
				if sensor['plugin']['name'] not in conf['plugins']:
					log.error("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] invalid plugin "+sensor['plugin']['name'])
					continue
				# handle push plugin
				if conf['plugins'][sensor['plugin']['name']]['type'] == "push":
					# register the sensor
					log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] registering with push service "+sensor['plugin']['name'])
					push_plugins[sensor['plugin']['name']].register_sensor(sensor)
				# handle pull plugin
                                else: 
					# schedule polling
					if sensor["refresh_interval_min"] == 0: continue
					log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling polling every "+str(sensor["refresh_interval_min"])+" minutes")
					# run it now first
					schedule.add_job(run,'date',run_date=datetime.datetime.now()+datetime.timedelta(seconds=utils.randint(1,59)),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'save'])
	                                # then schedule it for each refresh interval
	       	                        schedule.add_job(run,'cron',minute="*/"+str(sensor["refresh_interval_min"]),second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'save'])
                               	# schedule an expire job every day
                                schedule.add_job(run,'cron',hour="1",minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'expire'])
				# schedule a summarize job every hour and every day if needed
                                if sensor["calculate_avg"]:
               	                        log.debug("["+sensor['module_id']+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling summary every hour and day")
                      	                schedule.add_job(run,'cron',minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'summarize_hour'])
                              	        schedule.add_job(run,'cron',hour="0",minute="0",second=utils.randint(1,59),args=[sensor['module_id'],sensor['group_id'],sensor['sensor_id'],'summarize_day'])

# return the latest read of a sensor for a web request
def web_get_current(module_id,group_id,sensor_id):
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":sensors:"+group_id+":"+sensor_id
        # return the latest measure
        data = db.range(key,withscores=False,milliseconds=True)
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
	# if an image, decode it and return it
	if sensor["format"] == "image": return base64.b64decode(data[0])
	else: return json.dumps(data)

# return the latest image of a sensor for a web request
def web_get_current_image(module_id,group_id,sensor_id):
	data = json.loads(web_get_current(module_id,group_id,sensor_id))
	if len(data) == 0: return ""
	filename = "nt_"+data[0] if utils.is_night() else data[0]
	with open(conf["constants"]["web_dir"]+"/images/"+filename+".png",'r') as file:
                data = file.read()
        file.close()
	return data

# return the time difference between now and the latest measure
def web_get_current_timestamp(module_id,group_id,sensor_id):
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":sensors:"+group_id+":"+sensor_id
	data = db.range(key,withscores=True,milliseconds=True)
	if len(data) > 0: return json.dumps([utils.timestamp_difference(utils.now(),data[0][0]/1000)])
	else: return json.dumps(data)

# return the data of a requested sensor based on the timeframe and stat requested
def web_get_data(module_id,group_id,sensor_id,timeframe,stat):
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
                end = utils.day_start(utils.now()+(conf["web"]["forecast_timeframe_days"]-1)*conf["constants"]["1_day"])
                withscores = True
        else: return data
        # define the key to request
        key = conf["constants"]["db_schema"]["root"]+":"+module_id+":sensors:"+group_id+":"+sensor_id+range
        requested_stat = ":"+stat
        # if a range is requested, start asking for the min
        if stat == "range": requested_stat = ":min"
	if timeframe == "realtime": requested_stat = ""
        # requeste the data
        data = db.rangebyscore(key+requested_stat,start,end,withscores=withscores,milliseconds=True)
        if stat == "range" and len(data) > 0:
                # if a range is requested, ask for the max and combine the results
                data_max = db.rangebyscore(key+":max",start,end,withscores=False,milliseconds=True)
                for i, item in enumerate(data):
                        # ensure data_max has a correspondent value
                        if i < len(data_max):
                                if (isinstance(item,list)): data[i].append(data_max[i])
                                else: data.append(data_max[i])
        return json.dumps(data)

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
		run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

