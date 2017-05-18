#!/usr/bin/python
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import logging

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# default values for each job (30s tolerance to avoid missed job and put together multiple queued jobs)
job_defaults = {
	"coalesce": True,
	"misfire_grace_time": 30
}
# increas the thread pool executor to 20
executors = {
	"default": ThreadPoolExecutor(20),
	"processpool": ProcessPoolExecutor(10)
}
# create the scheduler which will run each job in background
scheduler = BackgroundScheduler(job_defaults=job_defaults, executors=executors)

# return the event name from an id
def get_event_name(code):
	if code == apscheduler.events.EVENT_SCHEDULER_STARTED: return "EVENT_SCHEDULER_STARTED"
	elif code == apscheduler.events.EVENT_SCHEDULER_SHUTDOWN: return "EVENT_SCHEDULER_SHUTDOWN"
	elif code == apscheduler.events.EVENT_SCHEDULER_PAUSED: return "EVENT_SCHEDULER_PAUSED"
	elif code == apscheduler.events.EVENT_SCHEDULER_RESUMED: return "EVENT_SCHEDULER_RESUMED"
	elif code == apscheduler.events.EVENT_EXECUTOR_ADDED: return "EVENT_EXECUTOR_ADDED"
	elif code == apscheduler.events.EVENT_EXECUTOR_REMOVED: return "EVENT_EXECUTOR_REMOVED"
	elif code == apscheduler.events.EVENT_JOBSTORE_ADDED: return "EVENT_JOBSTORE_ADDED"
	elif code == apscheduler.events.EVENT_JOBSTORE_REMOVED: return "EVENT_JOBSTORE_REMOVED"
	elif code == apscheduler.events.EVENT_ALL_JOBS_REMOVED: return "EVENT_ALL_JOBS_REMOVED"
	elif code == apscheduler.events.EVENT_JOB_ADDED: return "EVENT_JOB_ADDED"
	elif code == apscheduler.events.EVENT_JOB_REMOVED: return "EVENT_JOB_REMOVED"
	elif code == apscheduler.events.EVENT_JOB_MODIFIED: return "EVENT_JOB_MODIFIED"
	elif code == apscheduler.events.EVENT_JOB_SUBMITTED: return "EVENT_JOB_SUBMITTED"
	elif code == apscheduler.events.EVENT_JOB_MAX_INSTANCES: return "EVENT_JOB_MAX_INSTANCES"
	elif code == apscheduler.events.EVENT_JOB_EXECUTED: return "EVENT_JOB_EXECUTED"
	elif code == apscheduler.events.EVENT_JOB_ERROR: return "EVENT_JOB_ERROR"
	elif code == apscheduler.events.EVENT_JOB_MISSED: return "EVENT_JOB_MISSED"
	elif code == apscheduler.events.EVENT_ALL: return "EVENT_ALL"
	else: return "UNKNOWN"

# print out scheduler errors
def scheduler_error(code,event):
	job = scheduler.get_job(event.job_id)
	job_text = str(job.func_ref)+str(job.args) if job is not None else ""
	msg = get_event_name(code)+" for scheduled task "+job_text+": "
	if event.exception:
		msg = msg + "Exception "
		msg = msg +''.join(event.traceback)
		msg = msg.replace('\n','|')
		msg = msg + ": "+str(event.exception)
	else: 
		msg = msg + "No exception available"
	log.error(msg)

# handle scheduler errors
def on_job_missed(event):
	scheduler_error(apscheduler.events.EVENT_JOB_MISSED,event)
def on_job_error(event):
	scheduler_error(apscheduler.events.EVENT_JOB_ERROR,event)

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
scheduler.add_listener(on_job_missed, apscheduler.events.EVENT_JOB_MISSED)
scheduler.add_listener(on_job_error, apscheduler.events.EVENT_JOB_ERROR)

# return the scheduler object
def get_scheduler():
	return scheduler
