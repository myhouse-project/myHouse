#!/usr/bin/python
from apscheduler.schedulers.background import BackgroundScheduler

import utils
import sensors
import logger
import config
logger = logger.get_logger(__name__)
config = config.get_config()

scheduler = BackgroundScheduler()

def get_scheduler():
	return scheduler

