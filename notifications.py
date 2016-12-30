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
import notification_slack
import notification_email
import notification_sms

# schedule all reports
def schedule_all():
	# schedule module summary report
        for module in conf["modules"]:
		if not module["enabled"]: continue
		if "daily_digest" not in module: continue
                if conf["notifications"]["email"]["module_digest"] and module["daily_digest"]:
                        schedule.add_job(notification_email.module_digest,'cron',hour="23",minute="55",second=utils.randint(1,59),args=[module["module_id"]])
                        log.info("["+module['module_id']+"] scheduling daily module digest")
	# schedule alert summary report
	if conf["notifications"]["email"]["alerts_digest"]: 
		log.info("scheduling daily alert digest")
		schedule.add_job(notification_email.alerts_digest,'cron',hour="0",minute="55",args=[])
	# run slack bot
	if conf["notifications"]["slack"]["interactive_bot"]: schedule.add_job(notification_slack.run,'date',run_date=datetime.datetime.now())


# determine if a realtime notification has to be sent based on the severity and notification type
def realtime_notification(severity,type):
	# check if realtime alerts are enabled
	if not conf["notifications"][type]["realtime_alerts"]: return False
	# ensure the severity is equals or above the minimum severity configured
	min_severity = conf["notifications"][type]["severity"]
	if severity == "info" and min_severity in ["info","warning","alert"]:
	elif severity == "warning" and min_severity in ["warning","alert"]: return True
	elif severity == "alert" and min_severity in ["alert"]: return True
	return False

# notify all the registered plugins
def notify(severity,text):
	if realtime_notification(severity,"email"): notification_email.alert(text)
	if realtime_notification(severity,"slack"): notification_slack.says(text)
	if realtime_notification(severity,"sms"): notification_sms.send(text)

# main
if __name__ == '__main__':
       	if len(sys.argv) == 1:
                # no arguments provided, schedule all notifications
                schedule.start()
                schedule_all()
                while True:
                        time.sleep(1)
	else:
		if sys.argv[1] == "alerts_digest": notification_email.alerts_digest()
		elif sys.argv[1] == "module_digest": notification_email.module_digest(sys.argv[2])
		elif sys.argv[1] == "notify": notify(sys.argv[2])
		else: print "Usage: notifications.py <alerts_digest|module_digest|notify> [module_id]"
