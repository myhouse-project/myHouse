#!/usr/bin/python
import sys
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

# variables
db_alerts = conf["constants"]["db_schema"]["root"]+":alerts"
max_alerts = 5

# retrieve for the database the requested data
def get_data(module_id,request):
	key,start,end = request.split(',')
	key = conf["constants"]["db_schema"]["root"]+":"+module_id+":sensors:"+key
	return db.range(key,start=start,end=end,withscores=False)

# evaluate if a condition is met
def is_true(a,b,operator):
	evaluation = True
	# get a's value
	a = a[0]
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

# evaluate if the given alert has to trigger
def run(module_id,alert_id):
	module = utils.get_module(module_id)
	for alert in module["alerts"]:
		# retrive the alert for the given alert_id
        	if alert["alert_id"] != alert_id: continue
		# retrieve the data
		a = get_data(module_id,alert["condition"]["a"]) if ',' in alert["condition"]["a"] else alert["condition"]["a"]
		b = get_data(module_id,alert["condition"]["b"]) if ',' in alert["condition"]["b"] else alert["condition"]["b"]
		log.info("["+module_id+"]["+alert_id+"] evaluating "+str(a)+" "+alert["condition"]["operator"]+" "+str(b))
		# evaluate the condition
		if not is_true(a,b,alert["condition"]["operator"]): continue
		# prepare the alert text
		alert_text = alert["display_name"]
		alert_text = alert_text.replace("%a",str(a[0]))
		alert_text = alert_text.replace("%b",str(b[0]))
		# store the alert
		db.set(db_alerts,alert["severity"]+":"+alert_text,utils.now())
		log.info("["+module_id+"]["+alert_id+"]["+alert["severity"]+"] "+alert_text)
		
# run the given schedule
def run_schedule(run_every):
	# for each module
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
	schedule.add_job(run_schedule,'cron',hour="*",minute=utils.randint(2,5),args=["hour"])
	schedule.add_job(run_schedule,'cron',day="*",minute=utils.randint(2,5),args=["day"])

# return the latest alerts for a web request
def web_get_data():
	return json.dumps(db.range(db_alerts,-max_alerts,-1,milliseconds=True))

# allow running it both as a module and when called directly
if __name__ == '__main__':
        if len(sys.argv) != 3:
                # no arguments provided, schedule all alerts
                schedule.start()
                schedule_all()
                while True:
                        time.sleep(1)
        else:
                # run the command for the given alert
                run(sys.argv[1],sys.argv[2])


