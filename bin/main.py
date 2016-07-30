import sys
from time import sleep
import signal
import sys
import datetime
from multiprocessing import Process

import utils
import constants
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors
import scheduler
scheduler = scheduler.get_scheduler()
import web

# schedule each sensor 
def schedule_sensors():
	# for each module
	for module in constants.modules_with_sensors:
		# for each sensor
		for sensor_id in conf["modules"][module]["sensors"]:
			# for each serie
			for measure in conf["modules"][module]["sensors"][sensor_id]["measures"]:
				sensor = conf["modules"][module]["sensors"][sensor_id]["measures"][measure]
				log.info("["+module+"] Scheduling "+sensor_id+" "+measure+" polling every "+str(sensor["refresh_interval_min"])+" minutes")
				# schedule it
				scheduler.add_job(sensors.run,'cron',minute="*/"+str(sensor["refresh_interval_min"]),args=[module,sensor_id,measure,'read'])
				if constants.sensor_measures[measure]["avg"]:
					# if keep history, schedule a summarize job every hour and every day
					log.info("["+module+"] Scheduling "+sensor_id+" "+measure+" summary every hour and day")
					scheduler.add_job(sensors.run,'cron',hour="*",args=[module,sensor_id,measure,'summarize_hour'])
					scheduler.add_job(sensors.run,'cron',day="*",args=[module,sensor_id,measure,'summarize_day'])

# run the main application
def run():
	# schedule each sensor 
	scheduler.start()
	schedule_sensors()
	scheduler.add_job(web.run,'date',run_date=datetime.datetime.now())
	while True:
		sleep(1)
	# run the web server
#	web.run()
 
# allow running it both as a module and when called directly
if __name__ == "__main__":
	run()
