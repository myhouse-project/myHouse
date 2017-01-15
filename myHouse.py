#!/usr/bin/python
import time
import datetime
import sys

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors
import scheduler
schedule = scheduler.get_scheduler()
import webserver
import db
import alerter
import input
import pws

# run the main application
def run():
	log.info("Welcome to myHouse v"+conf["constants"]["version_string"])
	# initialize the database
	initialized = db.init()	
	if not initialized: sys.exit(1)
	# start the scheduler
	schedule.start()
	# schedule database backup
	db.schedule_all()
	# schedule all sensors
	if conf['sensors']['enabled']: sensors.schedule_all()
	# schedule all alerts
	if conf['alerter']['enabled']: alerter.schedule_all()
	# run all input services
	input.run()
	# start the web server
	if conf['gui']['enabled']: schedule.add_job(webserver.run,'date',run_date=datetime.datetime.now())
	# run the pws service
	if conf['pws']['enabled']: pws.schedule_all()
	# run as a deamon
	while True:
		time.sleep(1)
 
# allow running it both as a module and when called directly
if __name__ == "__main__":
	conf["constants"]["web_use_reloader"] = False
	run()
