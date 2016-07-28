import sys
from time import sleep
import signal
import sys
from multiprocessing import Process

import utils
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()
import sensors
import scheduler
scheduler = scheduler.get_scheduler()
import web

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

def shutdown(signal, frame):
	if scheduler.running: scheduler.shutdown()
	utils.get("http://localhost:8080/shutdown")
	logger.info("Exiting...")
        sys.exit(0)

def run():
#	signal.signal(signal.SIGINT,shutdown)
	schedule_sensors()
	scheduler.start()
	web.run()
 
# allow running it both as a module and when called directly
if __name__ == "__main__":
	run()
