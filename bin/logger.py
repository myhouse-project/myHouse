#!/usr/bin/python
import logging
import os

import config
conf = config.get_config()

# return the logger object
def get_logger(name):
	return logger

def get_console_logger(level):
	console = logging.StreamHandler()
	console.setLevel(level)
	console.setFormatter(conf["constants"]["logging"]["formatter"])
	return console

def get_file_logger(level,file):
	file = logging.FileHandler(file)
	file.setLevel(level)
	file.setFormatter(conf["constants"]["logging"]["formatter"])
	return file


# inizialize the logger
logger = logging.getLogger("myHouse")
logger.setLevel(conf["logging"]["level"]["myHouse"])
logger.addHandler(get_console_logger(conf["logging"]["level"]["myHouse"]))
logger.addHandler(get_file_logger(conf["logging"]["level"]["myHouse"],(conf["constants"]["logging"]["logfile"])))
