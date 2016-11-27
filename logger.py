#!/usr/bin/python
import logging 
import logging.handlers

import config
conf = config.get_config()

# return the logging level
def get_level(level):
	if level == "info": return logging.INFO
	elif level == "debug": return logging.DEBUG
	elif level == "warning": return logging.WARNING
	elif level == "error": return logging.ERROR
	elif level == "critical": return logging.CRITICAL
	else: return logging.INFO

# return the logger object
def get_logger(name):
	return logger

# return a console logger
def get_console_logger(logger_name):
	console = logging.StreamHandler()
	console.setLevel(get_level(conf["logging"][logger_name]["level"]))
	console.setFormatter(conf["constants"]["log_formatter"])
	return console

# return a file logger
def get_file_logger(logger_name):
	file = logging.handlers.RotatingFileHandler(conf["constants"]["log_dir"]+"/"+conf["logging"][logger_name]["filename"],maxBytes=conf["logging"]["rotate_size_mb"]*1024*1024, backupCount=conf["logging"]["rotate_count"])
	file.setLevel(get_level(conf["logging"][logger_name]["level"]))
	file.setFormatter(conf["constants"]["log_formatter"])
	return file

# inizialize the logger
logger_name = "myHouse"
logger = logging.getLogger(logger_name)
logger.setLevel(get_level(conf["logging"][logger_name]["level"]))
logger.addHandler(get_console_logger(logger_name))
logger.addHandler(get_file_logger(logger_name))
