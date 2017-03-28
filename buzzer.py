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
is_raspberry = utils.is_raspberry()

# setup the buzzer
if settings["enabled"]:
	# import GPIO module
	if is_raspberry: import RPi.GPIO as GPIO
	else: import OPi.GPIO as GPIO
	# initialize GPIO
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(settings["pin"], GPIO.OUT)

# send a sms with the given text
def notify(text):
        GPIO.output(settings["pin"], GPIO.HIGH)
        time.sleep(settings["duration"])
	GPIO.output(settings["pin"], GPIO.LOW)

# main
if __name__ == '__main__':
	notify("buzzer")
