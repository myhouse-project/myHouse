#!/usr/bin/python
from apscheduler.schedulers.background import BackgroundScheduler
import logging

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# configure a single background scheduler
scheduler = BackgroundScheduler()
# configure logging
logger_name = "scheduler"
scheduler_logger = logging.getLogger('apscheduler.executors.default')
scheduler_logger.setLevel(conf["logging"][logger_name]["level"])
scheduler_logger.addHandler(logger.get_console_logger(logger_name))
scheduler_logger.addHandler(logger.get_file_logger(logger_name))

# return the scheduler object
def get_scheduler():
	return scheduler

