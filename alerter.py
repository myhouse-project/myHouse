#!/usr/bin/python
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import time
import json

import utils
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()
import notification

# variables
max_alerts = 5

# retrieve for the database the requested data
def get_data(module_id,request):
	key,start,end = request.split(',')
	key = conf["constants"]["db_schema"]["root"]+":"+module_id+":sensors:"+key
	return db.range(key,start=start,end=end,withscores=False)

# evaluate if a condition is met
def is_true(a,operator,b):
	evaluation = True
	# get a's value
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
			if value >= a: evaluation = False
		elif operator == "<":
			if value <= a: evaluation = False
		else: evaluation = False
	# return the evaluation
	return evaluation

# determine if a statament is involving a sensor
def is_sensor(statement):
	if utils.is_number(statement): return False
	if ',' in statement: return True
	return False

# evaluate if the given alert has to trigger
def run(module_id,alert_id,fire=True):
	module = utils.get_module(module_id)
	for alert in module["alerts"]:
		# retrive the alert for the given alert_id
        	if alert["alert_id"] != alert_id: continue
		# for each statement retrieve the data
		statements = {}
		for statement in alert["statements"]:
			statements[statement] = get_data(module_id,alert["statements"][statement]) if is_sensor(alert["statements"][statement]) else alert["statements"][statement]
		# for each condition check if it is true
		evaluation = True
		for condition in alert["conditions"]:
			a,operator,b = condition.split(' ')
			sub_evaluation = is_true(statements[a],operator,statements[b])
			log.debug("["+module_id+"]["+alert_id+"] evaluating "+a+" ("+str(statements[a])+") "+operator+" "+b+" ("+str(statements[b])+"): "+str(sub_evaluation))
			if not sub_evaluation: evaluation = False
		log.debug("["+module_id+"]["+alert_id+"] evaluates to "+str(evaluation))
		# evaluate the conditions
		if not evaluation: continue
		# prepare the alert text
		alert_text = alert["display_name"]
		for statement in alert["statements"]:
			value = statements[statement][0] if isinstance(statements[statement],list) else statements[statement]
			# add the suffix
			if is_sensor(alert["statements"][statement]):
				key,start,end =  alert["statements"][statement].split(',')
				key_split = key.split(":")
				sensor = utils.get_sensor(module_id,key_split[0],key_split[1])
				if sensor is None:
					log.error("invalid sensor "+module_id+":"+key_split[0]+":"+key_split[1])
					return
				value = str(value)+conf["constants"]["formats"][sensor["format"]]["suffix"].encode('utf-8')
			alert_text = alert_text.replace("%"+statement+"%",str(value))
		# fire the alert
		if fire:
			db.set(conf["constants"]["db_schema"]["alerts"]+":"+alert["severity"],alert_text,utils.now())
			log.info("["+module_id+"]["+alert_id+"]["+alert["severity"]+"] "+alert_text)
			notification.notify(alert_text)	
		return alert_text
		
# run the given schedule
def run_schedule(run_every):
	# for each module
	log.debug("run alert configured by "+run_every)
        for module in conf["modules"]:
                if not module["enabled"]: continue
                if "alerts" not in module: continue
		# for each configured alert
                for alert in module["alerts"]:
			if alert["run_every"] != run_every: continue
			# evaluate it
			run(module["module_id"],alert["alert_id"])

# schedule both hourly and daily alerts
def schedule_all():
	log.info("starting alerter module...")
	schedule.add_job(run_schedule,'cron',minute="1",args=["hour"])
	schedule.add_job(run_schedule,'cron',hour="1",args=["day"])

# return the latest alerts for a web request
def web_get_data(severity,timeframe):
	start = utils.recent()
	if timeframe == "recent": start = utils.recent()
	if timeframe == "history": start = utils.history()
	return json.dumps(db.rangebyscore(conf["constants"]["db_schema"]["alerts"]+":"+severity,start,utils.now(),withscores=True,milliseconds=True))

# allow running it both as a module and when called directly
if __name__ == '__main__':
        if len(sys.argv) != 3:
                # no arguments provided, schedule all alerts
                schedule.start()
                schedule_all()
                while True:
                        time.sleep(1)
        else:
                # <module_id> <alert_id>
                run(sys.argv[1],sys.argv[2])


