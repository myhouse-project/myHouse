#!/usr/bin/python
import sys
import time
import datetime

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()
import output_slack
import output_email

# schedule all reports
def schedule_all():
	# schedule module summary report
        for module in conf["modules"]:
		if not module["enabled"]: continue
		if "daily_digest" not in module: continue
                if conf["notification"]["email"]["module_digest"] and module["daily_digest"]:
                        schedule.add_job(output_email.module_digest,'cron',hour="23",minute="55",second=utils.randint(1,59),args=[module["module_id"]])
                        log.info("["+module['module_id']+"] scheduling daily module digest")
	# schedule alert summary report
	if conf["notification"]["email"]["alerts_digest"]: 
		log.info("scheduling daily alert digest")
		schedule.add_job(output_email.alerts_digest,'cron',hour="0",minute="55",args=[])
	# run slack bot
	if conf["notification"]["slack"]["interactive_bot"]: schedule.add_job(output_slack.run,'date',run_date=datetime.datetime.now())


# notify all the registered plugins
def notify(text):
	if conf["notification"]["email"]["realtime_alerts"]: output_email.alert(text)
	if conf["notification"]["slack"]["realtime_alerts"]: output_slack.says(text)

# main
if __name__ == '__main__':
       	if len(sys.argv) == 1:
                # no arguments provided, schedule all notifications
                schedule.start()
                schedule_all()
                while True:
                        time.sleep(1)
	else:
		if sys.argv[1] == "alerts_digest": output_email.alerts_digest()
		elif sys.argv[1] == "module_digest": output_email.module_digest(sys.argv[2])
		elif sys.argv[1] == "notify": notify(sys.argv[2])
		else: print "Usage: notification.py <alerts_digest|module_digest|notify> [module_id]"
