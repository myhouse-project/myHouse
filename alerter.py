#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import time
import json
import datetime
import re
import copy
import base64
import cv2
import numpy
import os.path

import utils
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()
import notifications
import sensors

# for an image apply the configured object detection techniques
def parse_image(data):
	if len(data) != 1: return [""]
	# read the image
	data = base64.b64decode(data[0])
	image = numpy.asarray(bytearray(data), dtype="uint8")
	image = cv2.imdecode(image, cv2.IMREAD_COLOR)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# for each detection feature
	for feature in conf["alerter"]["object_detection"]:
		# load the cascade file
		filename = conf["constants"]["base_dir"]+"/"+feature["filename"]
		if not os.path.isfile(filename):
			log.error("Unable to load the detection object XML at "+filename)
			return [""]
		cascade = cv2.CascadeClassifier(filename)
		# perform detection
		objects = cascade.detectMultiScale(
			gray,
			scaleFactor=feature["scale_factor"],
			minNeighbors=feature["min_neighbors"],
			minSize=(feature["min_size"],feature["min_size"])
		)
		# nothing found, go to the next object
		if len(objects) == 0: continue
		# return the number of objects detected
		else: 
			if feature["save"]:
				# Draw a rectangle around the objects
				for (x, y, w, h) in objects:
					cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
				# save the image
				cv2.imwrite(conf["constants"]["tmp_dir"]+"/"+feature["object"]+".png",image)
			# return the alert text
			return [str(len(objects))+" "+feature["object"]]
	return [""]		

# for a location parse the data and return the label
def parse_position(data):
        if len(data) != 1: return []
        data = json.loads(data[0])
	return [data["label"]]

# for a calendar parse the data and return the value
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
                start_timestamp = utils.timezone(utils.timezone(int(time.mktime(start_date.timetuple()))))
                end_date = datetime.datetime.strptime(event["end_date"],"%Y-%m-%dT%H:%M:%S.000Z")
                end_timestamp = utils.timezone(utils.timezone(int(time.mktime(end_date.timetuple()))))
		now = utils.now()
		# check if we are within an event
		if now > start_timestamp and now < end_timestamp: return [event["text"]]
	return [0]

# retrieve for the database the requested data
def get_data(sensor,request):
	split = request.split(',')
	key = split[0]
	start = split[1]
	end = split[2]
	trasform = split[3] if len(split) > 3 else None
	key_split = key.split(":")
	# adjust start and end based on the request
	query = None
	if utils.is_number(start) and utils.is_number(end):
		# request range with start and end the relative positions
		query = db.range
	else:
		# request a timerange with start and end relative times from now
		query = db.rangebyscore
		start = utils.string2timestamp(start)
		end = utils.string2timestamp(end)
	# remove the module from the key
	key = key.replace(key_split[0]+":","",1)	
	key = conf["constants"]["db_schema"]["root"]+":"+key_split[0]+":"+key
	# handle special requests
	if trasform is not None and trasform == "elapsed":
		# retrieve the timestamp and calculate the time difference
		data = query(key,start=start,end=end,withscores=True)
		time_diff = (utils.now() - data[0][0])/60
		return [time_diff]
        if trasform is not None and trasform == "timestamp":
                # retrieve the timestamp 
                data = query(key,start=start,end=end,withscores=True)
                return [data[0][0]]
        elif trasform is not None and trasform == "distance":
                # calculate the distance between the point and our location
		data = query(key,start=start,end=end,withscores=False,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
		data = json.loads(data[0])
		distance = utils.distance([data["latitude"],data["longitude"]],[conf["general"]["latitude"],conf["general"]["longitude"]])
		return [int(distance)]
	else: 
		# just retrieve the data
		data = query(key,start=start,end=end,withscores=False,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
		if sensor["format"] == "calendar": data = parse_calendar(data)
		if sensor["format"] == "position": data = parse_position(data)
		if sensor["format"] == "image": data = parse_image(data)
	return data

# evaluate if a condition is met
def is_true(a,operator,b):
	evaluation = True
	# get a's value
	if not isinstance(a,list): a = [a]
	a = a[0]
	# prepare b's value
	if not isinstance(b,list): b = [b]
	# b can be have multiple values, cycle through all of them
	for value in b:
		if value is None or a is None: evaluation = False
		elif operator == "==":
			if value != a: evaluation = False
		elif operator == "!=":
			if value == a: evaluation = False
		elif operator == ">":
			if float(value) >= float(a): evaluation = False
		elif operator == "<":
			if float(value) <= float(a): evaluation = False
		else: evaluation = False
	# return the evaluation
	return evaluation

# determine if a definition is involving a sensor
def is_sensor(definition):
	if utils.is_number(definition): return False
	if ',' in definition: return True
	if ':' in definition: return True
	return False

# evaluate if the given alert has to trigger
def run(module_id,rule_id,notify=True):
	alert_text = ""
	try: 
		module = utils.get_module(module_id)
		for rule_template in module["rules"]:
			if not rule_template["enabled"]: continue
			# retrive the rule for the given rule_id
	        	if rule_template["rule_id"] != rule_id: continue
			# for each variable (if provided) run a different evaluation
			variables = [""]
			variable_sensor = None
			if "for" in rule_template: variables = rule_template["for"]
			for variable in variables:
				# ensure the variable is a valid sensor
				if variable != '' and is_sensor(variable):
					variable_split = variable.split(":")
					variable_sensor = utils.get_sensor(variable_split[0],variable_split[1],variable_split[2])
					if variable_sensor is None:
						log.error("invalid variable sensor "+variable)
                                                continue
				# restore the template
				rule = copy.deepcopy(rule_template)
				# for each definition retrieve the data
				definitions = {}
				suffix = {}
				valid_data = True
				for definition in rule["definitions"]:
					if is_sensor(rule["definitions"][definition]):
						rule["definitions"][definition] = rule["definitions"][definition].replace("%i%",variable)
						# check if the sensor exists
						split = rule["definitions"][definition].split(',')
						key = split[0]
						start = split[1]
						end = split[2]
			                        key_split = key.split(":")
			                        sensor = utils.get_sensor(key_split[0],key_split[1],key_split[2])
			                        if sensor is None:
			                        	log.error("invalid sensor "+key_split[0]+":"+key_split[1]+":"+key_split[2])
							valid_data = False
			                                break
						# retrieve and store the data
						definitions[definition] = get_data(sensor,rule["definitions"][definition])
						if len(definitions[definition]) == 0: 
							log.debug("invalid data from sensor "+key)
							valid_data = False
							break
						# store the suffix
						suffix[definition] = conf["constants"]["formats"][sensor["format"]]["suffix"].encode('utf-8')
					else: 
						definitions[definition] = rule["definitions"][definition]
				# if not all the data is valid, return
				if not valid_data: continue
				# for each condition check if it is true
				evaluation = True
				for condition in rule["conditions"]:
					condition = re.sub(' +',' ',condition)
					a,operator,b = condition.split(' ')
					sub_evaluation = is_true(definitions[a],operator,definitions[b])
					log.debug("["+module_id+"]["+rule_id+"] evaluating "+a+" ("+str(definitions[a])+") "+operator+" "+b+" ("+str(definitions[b])+"): "+str(sub_evaluation))
					if not sub_evaluation: evaluation = False
				log.debug("["+module_id+"]["+rule_id+"] evaluates to "+str(evaluation))
				# evaluate the conditions
				if not evaluation: continue
				# alert has triggered, prepare the alert text
				alert_text = rule["display_name"]
				# replace the variable if needed
				if variable_sensor is not None: alert_text = alert_text.replace("%i%",variable_sensor["display_name"])
				# replace the definitions placeholders
				for definition in rule["definitions"]:
					value = definitions[definition][0] if isinstance(definitions[definition],list) else definitions[definition]
					# add the suffix
					if is_sensor(rule["definitions"][definition]) and "elapsed" in rule["definitions"][definition]: 
						value = str(value)+" minutes"
                                       	if is_sensor(rule["definitions"][definition]) and "timestamp" in rule["definitions"][definition]:
                                                value = utils.timestamp2date(value)
					if is_sensor(rule["definitions"][definition]) and "distance" in rule["definitions"][definition]:
						if conf["general"]["units"]["imperial"]: value = str(value)+" miles"
						else: value = str(value)+" km"
					elif is_sensor(rule["definitions"][definition]): value = str(value)+suffix[definition]
					alert_text = alert_text.replace("%"+definition+"%",str(value))
				# execute an action
				if "actions" in rule:
					for action in rule["actions"]:
						# replace the definitions placeholders
						action = action.replace("%i%",variable)
						for definition in rule["definitions"]:
							value = definitions[definition][0] if isinstance(definitions[definition],list) else definitions[definition]
							action = action.replace("%"+definition+"%",str(value))
						# parse the action
						split = action.split(',')
					        what = split[0]
					        key = split[1]
					        value = split[2]
					        force = True if len(split) > 3 and split[3] == "force" else False
						ifnotexists = True if len(split) > 3 and split[3] == "ifnotexists" else False
						# ensure the target sensor exists
						key_split = key.split(":")
						sensor = utils.get_sensor(key_split[0],key_split[1],key_split[2])
						if sensor is None: 
							log.warning("["+rule["rule_id"]+"] invalid sensor "+key)
							continue
						# execute the requested action
						if what == "send": sensors.data_send(key_split[0],key_split[1],key_split[2],value,force=force)
						elif what == "set": sensors.data_set(key_split[0],key_split[1],key_split[2],value,ifnotexists=ifnotexists)
				# notify about the alert
				if rule["severity"] == "none": notify = False
				if notify:
					log.info("["+module_id+"]["+rule_id+"]["+rule["severity"]+"] "+alert_text)
					if rule["severity"] != "debug":
						db.set(conf["constants"]["db_schema"]["alerts"]+":"+rule["severity"],alert_text,utils.now())
						notifications.notify(rule["severity"],alert_text)
        except Exception,e:
                log.warning("error while running rule "+module_id+":"+rule_id+": "+utils.get_exception(e))
	return alert_text


# purge old data from the database
def expire():
        total = 0
        for stat in [':alert',':warning',':info']:
                key = conf["constants"]["db_schema"]["alerts"]+stat
                if db.exists(key):
                        deleted = db.deletebyscore(key,"-inf",utils.now()-conf["alerter"]["data_expire_days"]*conf["constants"]["1_day"])
                        log.debug("expiring from "+stat+" "+str(total)+" items")
                        total = total + deleted
        log.info("expired "+str(total)+" items")
		
# run the given schedule
def run_schedule(run_every):
	# for each module
	log.debug("evaluate all the rules configured to run every "+run_every)
        for module in conf["modules"]:
                if not module["enabled"]: continue
                if "rules" not in module: continue
                # for each configured rule
                for rule in module["rules"]:
                        if not rule["enabled"]: continue
			if rule["run_every"] != run_every: continue
			# if the rule has the given run_every, run it
			run(module["module_id"],rule["rule_id"])

# schedule both hourly and daily alerts
def schedule_all():
	log.info("starting alerter module...")
	# run now startup rules
        schedule.add_job(run_schedule,'date',run_date=datetime.datetime.now(),args=["startup"])
	# schedule minute, hourly and daily jobs
	schedule.add_job(run_schedule,'cron',second="30",args=["minute"])
	schedule.add_job(run_schedule,'cron',minute="*/5",args=["5 minutes"])
	schedule.add_job(run_schedule,'cron',minute="*/10",args=["10 minutes"])
	schedule.add_job(run_schedule,'cron',minute="*/30",args=["30 minutes"])
	schedule.add_job(run_schedule,'cron',minute="1",args=["hour"])
	schedule.add_job(run_schedule,'cron',hour="1",args=["day"])
	# schedule an expire job
	schedule.add_job(expire,'cron',hour="1")

# return the latest alerts for a web request
def data_get_alerts(severity,timeframe):
	start = utils.recent()
	if timeframe == "recent": start = utils.recent(hours=conf["general"]["timeframes"]["alerter_recent_hours"])
	if timeframe == "history": start = utils.history(days=conf["general"]["timeframes"]["alerter_history_days"])
	return json.dumps(db.rangebyscore(conf["constants"]["db_schema"]["alerts"]+":"+severity,start,utils.now(),withscores=True,format_date=True))

# allow running it both as a module and when called directly
if __name__ == '__main__':
        if len(sys.argv) != 3:
                # no arguments provided, schedule all alerts
                schedule.start()
                schedule_all()
                while True:
                        time.sleep(1)
        else:
                # <module_id> <rule_id>
                run(sys.argv[1],sys.argv[2])
