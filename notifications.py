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
import notification_audio

# variables
current_hour = None
counters = {}
channels = {
	"email": notification_email,
	"slack": notification_slack,
	"sms": notification_sms,
	"audio": notification_audio
}

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

# notify all the notification channels
def notify(severity,text):
	global current_hour, notifications, channels
	# retrieve the current hour
	hour = int(time.strftime("%H"))
	# if this is a new hour, reset the notification counters
	if hour is None or current_hour != hour:
		for channel in channels: counters[channel] = 0
		current_hour = hour
	# for each channel to be notified
	for channel,module in channels.iteritems():
		# ensure realtime alerts are enabled
		if not conf["notifications"][channel]["realtime_alerts"]: continue
		# ensure the severity is equals or above the minimum severity configured
		min_severity = conf["notifications"][channel]["severity"]
		if min_severity == "warning" and severity in ["info"]: continue
		elif min_severity == "alert" and severity in ["info","warning"]: continue
		# ensure the channel is not mute during this time
		if "-" in conf["notifications"][channel]["mute"]:
			timeframe = conf["notifications"][channel]["mute"].split("-")
			if len(timeframe) != 2: continue
			timeframe[0] = int(timeframe[0])
			timeframe[1] = int(timeframe[1])
			# e.g. 08-12
			if timeframe[0] < timeframe[1] and (hour >= timeframe[0] and hour < timeframe[1]): continue
			# e.g. 20-07
			if timeframe[0] > timeframe[1] and (hour >= timeframe[0] or hour < timeframe[1]): continue
		# check if rate limit is configured and we have not exceed the numner of notifications during this hour
		if conf["notifications"][channel]["rate_limit"] != 0 and counters[channel] >= conf["notifications"][channel]["rate_limit"]: continue
		# send the notification to the channel
		module.notify(text)
		# increase the counter
		counters[channel] = counters[channel] + 1
		log.debug("Notification channel "+channel+" sent so far "+str(counters[channel])+" notifications during hour "+current_hour+" with limit "+str(conf["notifications"][channel]["rate_limit"]))

# main
if __name__ == '__main__':
	schedule.start()
        schedule_all()
       	while True:
               	time.sleep(1)
