#!/usr/bin/python
import sys
import time
import datetime

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import slack
import smtp
import sms
import audio

# variables
current_hour = None
counters = {}
channels = {
	"email": smtp,
	"slack": slack,
	"sms": sms,
	"audio": audio
}

# notify all the notification channels
def notify(severity,text):
	global current_hour, channels, counters
	# retrieve the current hour
	hour = int(time.strftime("%H"))
	# if this is a new hour, reset the notification counters
	if hour is None or current_hour != hour:
		for channel in channels: counters[channel] = 0
		current_hour = hour
	# for each channel to be notified
	for channel,module in channels.iteritems():
		# ensure realtime alerts are enabled
		if not conf["output"][channel]["enabled"]: continue
		mute_override = False
		min_severity = None
		mute_min_severity = None
		# ensure the severity is equals or above the minimum severity configured
		if "min_severity" in conf["output"][channel]:
			min_severity = conf["output"][channel]["min_severity"]
			if min_severity == "warning" and severity in ["info"]: continue
			elif min_severity == "alert" and severity in ["info","warning"]: continue
		# check if the notification is severe enough to override the mute setting
		if "mute_min_severity" in conf["output"][channel]:
			mute_min_severity = conf["output"][channel]["mute_min_severity"]
			if mute_min_severity == "warning" and severity in ["warning","alert"]: mute_override = True
			elif mute_min_severity == "alert" and severity in ["alert"]: mute_override = True
		# ensure the channel is not mute now
		if "mute" in conf["output"][channel] and "-" in conf["output"][channel]["mute"] and not mute_override:
			timeframe = conf["output"][channel]["mute"].split("-")
			if len(timeframe) != 2: continue
			timeframe[0] = int(timeframe[0])
			timeframe[1] = int(timeframe[1])
			# e.g. 08-12
			if timeframe[0] < timeframe[1] and (hour >= timeframe[0] and hour < timeframe[1]): continue
			# e.g. 20-07
			if timeframe[0] > timeframe[1] and (hour >= timeframe[0] or hour < timeframe[1]): continue
		# check if rate limit is configured and we have not exceed the numner of notifications during this hour
		if "rate_limit" in conf["output"][channel] and conf["output"][channel]["rate_limit"] != 0 and counters[channel] >= conf["output"][channel]["rate_limit"]: continue
		# increase the counter
		counters[channel] = counters[channel] + 1
		log.debug(channel+" notifications: "+str(counters[channel])+" for "+str(current_hour)+":00")
		# send the notification to the channel
		try: 
			# catch exceptions in order to notify even if a channel will fail
			module.notify(text)
		except Exception,e:
			log.error("unable to notify through "+channel+": "+utils.get_exception(e))

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: "+__file__+" <severity> <message>"
	else:
		notify(sys.argv[1],sys.argv[2])
