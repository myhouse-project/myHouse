#!/usr/bin/python
import sys
import time

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["buzzer"]
platform = utils.get_platform()
supported_platform = True if platform != "unknown" else False

# setup the buzzer
if settings["enabled"]:
	# import GPIO module
	if platform == "raspberry_pi": import RPi.GPIO as GPIO
	elif platform == "orange_pi": import OPi.GPIO as GPIO
	# initialize GPIO
	if supported_platform:
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(settings["pin"], GPIO.OUT)

# send a sms with the given text
def notify(text):
	if settings["enabled"] and supported_platform:
	        GPIO.output(settings["pin"], GPIO.HIGH)
	        time.sleep(settings["duration"])
		GPIO.output(settings["pin"], GPIO.LOW)

# main
if __name__ == '__main__':
	notify("buzzer")
