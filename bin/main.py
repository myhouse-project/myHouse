import sys
from time import sleep

import utils
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()
import sensors
import scheduler
scheduler = scheduler.get_scheduler()

modules_with_sensors = ['weather']

def schedule_sensors():
	for module in modules_with_sensors:
		for sensor_id in config["modules"][module]["sensors"]:
			for measure in config["modules"][module]["sensors"][sensor_id]["series"]:
				sensor = config["modules"][module]["sensors"][sensor_id]["series"][measure]
				logger.info("["+module+"] Scheduling "+sensor_id+" "+measure+" every "+str(sensor["refresh_interval_min"])+" minutes, keep history="+str(sensor["keep_history"]))
				scheduler.add_job(sensors.run,'cron',minute="*/"+str(sensor["refresh_interval_min"]),args=[module,sensor_id,measure,'save'])
				if sensor["keep_history"]:
					scheduler.add_job(sensors.run,'cron',hour="*",args=[module,sensor_id,measure,'summarize_hour'])
					scheduler.add_job(sensors.run,'cron',day="*",args=[module,sensor_id,measure,'summarize_day'])

def run():
	schedule_sensors()
	scheduler.start()
	while True:
		sleep(1)
#    job = sched.add_job(my_job,'cron', second="*/5", args=['text1'])
#    job = sched.add_job(my_job,'cron', second="*/2", args=['text2'])
 
# allow running it both as a module and when called directly
if __name__ == "__main__":
	run()
