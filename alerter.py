#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import time
import json
import datetime
import re
import copy

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

# variables
rules = {
	"hour": [],
	"day": [],
	"minute": [],
	"startup": [],
}
minutes_since = "timestamp"

# for a calendar parse the data and return the value
def parse_calendar(data):
	# the calendar string is at position 0
	if len(data) != 1: return
	data = json.loads(data[0])
	# the list of events is at position 1
	if len(data) != 2: return
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
	# remove the module from the key
	key = key.replace(key_split[0]+":","",1)	
	key = conf["constants"]["db_schema"]["root"]+":"+key_split[0]+":"+key
	if trasform is not None and trasform == minutes_since:
		# retrieve the timestamp and calculate the time difference
		data = db.range(key,start=start,end=end,withscores=True)
		time_diff = (utils.now() - data[0][0])/60
		return [time_diff]
	else: 
		# just retrieve the data
		data = db.range(key,start=start,end=end,withscores=False,formatter=conf["constants"]["formats"][sensor["format"]]["formatter"])
	if sensor["format"] == "calendar": data = parse_calendar(data)
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
		if operator == "==":
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
				if variable != "":
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
					if is_sensor(rule["definitions"][definition]) and minutes_since in rule["definitions"][definition]: value = str(value)+" minutes"
					elif is_sensor(rule["definitions"][definition]): value = str(value)+suffix[definition]
					alert_text = alert_text.replace("%"+definition+"%",str(value))
				# execute an action
				if "actions" in rule:
					for action in rule["actions"]:
						action = action.replace("%i%",variable)
						split = action.split(',')
					        what = split[0]
					        key = split[1]
					        value = split[2]
					        force = True if len(split) > 3 and split[3] == "force" else False
						# ensure the target sensor exists
						key_split = key.split(":")
						sensor = utils.get_sensor(key_split[0],key_split[1],key_split[2])
						if sensor is None: 
							log.warning("["+rule["rule_id"]+"] invalid sensor "+key)
							continue
						# execute the requested action
						if what == "send": sensors.data_send(key_split[0],key_split[1],key_split[2],value,force=force)
						elif what == "set": sensors.data_set(key_split[0],key_split[1],key_split[2],value)
				# notify about the alert
				if rule["severity"] == "none": notify = False
				if notify:
					log.info("["+module_id+"]["+rule_id+"]["+rule["severity"]+"] "+alert_text)
					if rule["severity"] != "debug":
						db.set(conf["constants"]["db_schema"]["alerts"]+":"+rule["severity"],alert_text,utils.now())
						notifications.notify(alert_text)
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
	for rule in rules[run_every]:
		run(rule[0],rule[1])

# schedule both hourly and daily alerts
def schedule_all():
	log.info("starting alerter module...")
	# organize all the configured rules
        for module in conf["modules"]:
                if not module["enabled"]: continue
                if "rules" not in module: continue
                # for each configured rule
                for rule in module["rules"]:
			if not rule["enabled"]: continue
			if rule["run_every"] != "hour" and rule["run_every"] != "day" and rule["run_every"] != "minute" and rule["run_every"] != "startup": continue
			rules[rule["run_every"]].append([module["module_id"],rule["rule_id"]])
        # run startup alerts
        schedule.add_job(run_schedule,'date',run_date=datetime.datetime.now(),args=["startup"])
	# schedule minute, hourly and daily jobs
	schedule.add_job(run_schedule,'cron',second="30",args=["minute"])
	schedule.add_job(run_schedule,'cron',minute="1",args=["hour"])
	schedule.add_job(run_schedule,'cron',hour="1",args=["day"])
	# schedule an expire job
	schedule.add_job(expire,'cron',hour="1")

# return the latest alerts for a web request
def data_get_alerts(severity,timeframe):
	start = utils.recent()
	if timeframe == "recent": start = utils.recent(hours=conf["timeframes"]["alerter_recent_hours"])
	if timeframe == "history": start = utils.history(days=conf["timeframes"]["alerter_history_days"])
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
