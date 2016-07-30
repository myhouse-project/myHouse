#!/usr/bin/python
import logging
import os

import constants
import utils
import config
conf = config.get_config()

# return the logger object
def get_logger(name):
	return logger

def get_console_logger(level):
	console = logging.StreamHandler()
	console.setLevel(level)
	console.setFormatter(constants.log_formatter)
	return console

def get_file_logger(level,file):
	file = logging.FileHandler(file)
	file.setLevel(level)
	file.setFormatter(constants.log_formatter)
	return file


# inizialize the logger
logger = logging.getLogger("myHouse")
logger.setLevel(conf["logging"]["level"]["myHouse"])
logger.addHandler(get_console_logger(conf["logging"]["level"]["myHouse"]))
logger.addHandler(get_file_logger(conf["logging"]["level"]["myHouse"],constants.log_file))
