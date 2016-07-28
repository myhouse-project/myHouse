#!/usr/bin/python
import logging
import os

import config
config = config.get_config()

formatter = logging.Formatter('[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s',"%Y-%m-%d %H:%M:%S")

def get_logger(name):
	return logger

def get_log_path():
	return os.path.abspath(os.path.dirname(__file__))+"/../logs/"

logger = logging.getLogger("myHouse")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

file = logging.FileHandler(get_log_path()+"myHouse.log")
file.setLevel(logging.DEBUG)
file.setFormatter(formatter)
logger.addHandler(file)


