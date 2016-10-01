#!/usr/bin/python
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
import logging

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
scheduler = BackgroundScheduler()

# handle scheduler errors
def error_listener(event):
	job = scheduler.get_job(event.job_id)
	msg = "unable to run scheduled task "+str(job.func_ref)+str(job.args)+": "
	if event.exception:
		msg = msg + "Exception "
		msg = msg +''.join(event.traceback)
		msg = msg.replace('\n','|')
		msg = msg + ": "+str(event.exception)
	else: 
		msg = msg + "Error"
	log.error(msg)

# configure logging
logger_name = "scheduler"
scheduler_logger = logging.getLogger('apscheduler.executors.default')
scheduler_logger.setLevel(logger.get_level(conf["logging"][logger_name]["level"]))
scheduler_logger.addHandler(logger.get_console_logger(logger_name))
scheduler_logger.addHandler(logger.get_file_logger(logger_name))

scheduler_logger = logging.getLogger('apscheduler.scheduler')
scheduler_logger.setLevel(logger.get_level(conf["logging"][logger_name]["level"]))
scheduler_logger.addHandler(logger.get_console_logger(logger_name))
scheduler_logger.addHandler(logger.get_file_logger(logger_name))

# handle errors and exceptions
scheduler.add_listener(error_listener, apscheduler.events.EVENT_JOB_MISSED | apscheduler.events.EVENT_JOB_ERROR)

# return the scheduler object
def get_scheduler():
	return scheduler
