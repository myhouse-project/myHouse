#!/usr/bin/python
import logging 

import config
conf = config.get_config()

# return the logger object
def get_logger(name):
	return logger

def get_console_logger(logger_name):
	console = logging.StreamHandler()
	console.setLevel(conf["logging"][logger_name]["level"])
	console.setFormatter(conf["constants"]["log_formatter"])
	return console

def get_file_logger(logger_name):
	file = logging.FileHandler(conf["constants"]["log_dir"]+conf["logging"][logger_name]["filename"])
	file.setLevel(conf["logging"][logger_name]["level"])
	file.setFormatter(conf["constants"]["log_formatter"])
	return file


# inizialize the logger
logger_name = "myHouse"
logger = logging.getLogger(logger_name)
logger.setLevel(conf["logging"][logger_name]["level"])
logger.addHandler(get_console_logger(logger_name))
logger.addHandler(get_file_logger(logger_name))
