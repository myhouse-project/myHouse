#!/usr/bin/python
import sys
import os
import datetime

import utils
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()

import sensor_ds18b20
import sensor_wunderground
import sensor_weatherchannel
import sensor_linux

# read data out of a sensor and store the output in the cache
def poll(plugin,sensor):
	# poll the data
	data = None
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] polling sensor")
        try: 
		# retrieve the raw data 
		data = plugin.poll(sensor)
	        # store it in the cache
	        db.set(sensor["db_cache"],data,utils.now())
	except Exception,e: 
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to poll: "+utils.get_exception(e))
	return data

# parse the data of a sensor from the cache and return the value read
def parse(plugin,sensor):
	# retrieve the raw data from the cache
	data = db.range(sensor["db_cache"],withscores=False)[0]
	measures = None
        try:
		# parse the cached data
		measures = plugin.parse(sensor,data)
		# format each values
		for i in range(len(measures)): measures[i]["value"] = utils.normalize(measures[i]["value"])
		log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] parsed: "+str(measures))
	except Exception,e:
		log.warning("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] unable to parse "+str(data)+": "+utils.get_exception(e))
	# return the structured data
	return measures

# save the data of a sensor into the database
def save(plugin,sensor):
	cache_timestamp = 0
	# get the raw data from the cache
	if db.exists(sensor["db_cache"]):
		data = db.range(sensor["db_cache"],withscores=True)
		cache_timestamp = data[0][0]
	# if too old, refresh it
	if utils.now() - cache_timestamp > conf['modules'][sensor["module"]]['cache_valid_for_seconds']:
		# if an exception occurred, skip this sensor
		if poll(plugin,sensor) is None: return
	# get the parsed data
	measures = parse(plugin,sensor)
	# if an exception occurred, skip this sensor
	if measures is None: return
	# for each returned measure
	for measure in measures:
	        # set the timestamp to now if not already set
	        if "timestamp" not in measure:  measure["timestamp"] = utils.now()
		# define the key to store the value
		key = sensor["db_group"]+":"+measure["key"]
		# delete previous values if no history has to be kept (e.g. single value)
		#if not sensor["calculate_avg"]: db.delete(key)
		# check if the same value is already stored
		old = db.rangebyscore(key,measure["timestamp"],measure["timestamp"])
		if len(old) > 0:
			# same value and same timestamp, do not store
			log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") ignoring "+measure["key"]+": "+str(measure["value"]))
			return
		# store the value into the database
		log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(measure["timestamp"])+") saving "+measure["key"]+": "+utils.truncate(str(measure["value"])))
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
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] ("+utils.timestamp2date(timestamp)+") updating summary of the "+timeframe+" (min,avg,max): ("+str(min)+","+str(avg)+","+str(max)+")")

# purge old data from the database
def expire(sensor):
	total = 0
	for stat in ["",':hour:min',':hour:avg',':hour:max']:
		key = sensor['db_sensor']+stat
		if db.exists(key):
			deleted = db.deletebyscore(key,"-inf",utils.now()-conf["constants"]["expire_days"]*conf["constants"]["1_day"])
			log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expiring from "+stat+" "+str(total)+" items")
			total = total + deleted
	log.info("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] expired "+str(total)+" items")

# read or save the measure of a given sensor
def run(module,group_id,sensor_id,action):
	# ensure the group and sensor exist
	sensor = None
	if module not in conf['modules']: log.error("["+module+"] not configured")
	for this_group in conf['modules'][module]['sensor_groups']:
		if this_group['group_id'] != group_id: continue
		for this_sensor in this_group['sensors']:
			if this_sensor['sensor_id'] != sensor_id: continue
			else: 
				sensor = this_sensor
				sensor['module'] = module
				sensor['group_id'] = this_group['group_id']
				break
	if sensor is None: log.error("["+module+"]["+group_id+"]["+sensor_id+"] not configured")
        # determine the plugin to use 
	if sensor["plugin"] == "ds18b20": plugin = sensor_ds18b20
        elif sensor["plugin"] == "wunderground": plugin = sensor_wunderground
	elif sensor["plugin"] == "weatherchannel": plugin = sensor_weatherchannel
	elif sensor["plugin"] == "linux": plugin = sensor_linux
	else: log.error("Plugin "+sensor["plugin"]+" not supported")
	# define the database schema
        sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module"]+":sensors:"+sensor["group_id"]
	sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
        sensor['db_cache'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module"]+":__cache__:"+sensor["group_id"]+":"+sensor["plugin"]+"_"+plugin.cache_schema(sensor["request"])
	# execute the action
	log.debug("["+sensor["module"]+"]["+sensor["group_id"]+"]["+sensor["sensor_id"]+"] requested "+action)
	if action == "poll":
		# delete from the cache the previous value 
		db.delete(sensor['db_cache'])
		# read the measure (will be stored into the cache)
		poll(plugin,sensor)
	elif action == "parse":
		# just parse the output
		parse(plugin,sensor)
	elif action == "save":
		# save the parsed output into the database
		save(plugin,sensor)
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

# schedule each sensor
def schedule_all():
        # for each module
        for module in conf["modules"]:
		# skip modules without sensors
		if "sensor_groups" not in conf["modules"][module]: continue
	        # for each group of sensors
                for group in conf["modules"][module]["sensor_groups"]:
			# for each sensor of the group
			for sensor in group["sensors"]:
				sensor['module'] = module
				sensor['group_id'] = group['group_id']
                                log.info("["+module+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling polling every "+str(sensor["refresh_interval_min"])+" minutes")
				# run it now first
				schedule.add_job(run,'date',run_date=datetime.datetime.now()+datetime.timedelta(seconds=utils.randint(1,59)),args=[module,sensor['group_id'],sensor['sensor_id'],'save'])
                                # then schedule it for each refresh interval
       	                        schedule.add_job(run,'cron',minute="*/"+str(sensor["refresh_interval_min"]),second=utils.randint(1,59),args=[module,sensor['group_id'],sensor['sensor_id'],'save'])
				# schedule an expire job every day
				schedule.add_job(run,'cron',day="*",args=[module,sensor['group_id'],sensor['sensor_id'],'expire'])
                                if sensor["calculate_avg"]:
       	                                # schedule a summarize job every hour and every day
               	                        log.info("["+module+"]["+sensor['group_id']+"]["+sensor['sensor_id']+"] scheduling summary every hour and day")
                       	                schedule.add_job(run,'cron',hour="*",second=utils.randint(1,59),args=[module,sensor['group_id'],sensor['sensor_id'],'summarize_hour'])
                               	        schedule.add_job(run,'cron',day="*",second=utils.randint(1,59),args=[module,sensor['group_id'],sensor['sensor_id'],'summarize_day'])

# return the latest read of a sensor for a web request
def web_get_current(module,group_id,sensor_id):
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
        # return the latest measure
        data = db.range(key,withscores=False,milliseconds=True)
	return data

# return the time difference between now and the latest measure
def web_get_current_timestamp(module,group_id,sensor_id):
        data = []
        key = conf["constants"]["db_schema"]["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
	data = db.range(key,withscores=True,milliseconds=True)
	if len(data) > 0: return [utils.timestamp_difference(utils.now(),data[0][0]/1000)]
	else: return data

# return the data of a requested sensor based on the timeframe and stat requested
def web_get_data(module,group_id,sensor_id,timeframe,stat):
        data = []
        # get the parameters for the requested timeframe
        if timeframe == "recent":
                # recent hourly measures up to now
                range = "hour"
                start = utils.recent()
                end = utils.now()
                withscores = True
        elif timeframe == "history":
                # historical daily measures up to new
                range = "day"
                start = utils.history()
                end = utils.now()
                withscores = True
        elif timeframe == "today":
                # today's measure
                range = "day"
                start = utils.day_start(utils.now())
                end = utils.day_end(utils.now())
                withscores = False
        elif timeframe == "yesterday":
                # yesterday's measure
                range = "day"
                start = utils.day_start(utils.yesterday())
                end = utils.day_end(utils.yesterday())
                withscores = False
	elif timeframe == "forecast":
		# next days measures
                range = "day"
                start = utils.day_start(utils.now())
                end = utils.day_start(utils.now()+(conf["charts"]["forecast_timeframe_days"]-1)*conf["constants"]["1_day"])
                withscores = True
        else: return data
        # define the key to request
        key = conf["constants"]["db_schema"]["root"]+":"+module+":sensors:"+group_id+":"+sensor_id+":"+range
        requested_stat = stat
        # if a range is requested, start asking for the min
        if stat == "range": requested_stat = "min"
        # requeste the data
        data = db.rangebyscore(key+":"+requested_stat,start,end,withscores=withscores,milliseconds=True)
        if stat == "range" and len(data) > 0:
                # if a range is requested, ask for the max and combine the results
                data_max = db.rangebyscore(key+":max",start,end,withscores=False,milliseconds=True)
                for i, item in enumerate(data):
                        # ensure data_max has a correspondent value
                        if i < len(data_max):
                                if (isinstance(item,list)): data[i].append(data_max[i])
                                else: data.append(data_max[i])
        return data

# allow running it both as a module and when called directly
if __name__ == '__main__':
	if (len(sys.argv) != 5): print "Usage: sensors.py <module> <group_id> <sensor_id> <action>"
	else: run(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

