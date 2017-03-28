#!/usr/bin/python
import sys
import time

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

is_raspberry = utils.is_raspberry()

# initialize the buzzer
if is_raspberry:
	import RPi.GPIO as GPIO
	settings = conf["output"]["buzzer"]
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(settings["pin"], GPIO.OUT)

# send a sms with the given text
def notify(text):
	if not is_raspberry: return
        GPIO.output(settings["pin"], GPIO.HIGH)
        time.sleep(settings["duration"])
	GPIO.output(settings["pin"], GPIO.LOW)

# main
if __name__ == '__main__':
	notify("buzzer")
