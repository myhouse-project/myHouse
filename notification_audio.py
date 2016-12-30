#!/usr/bin/python
import sys

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["notifications"]["audio"]
filename = "/tmp/myHouse.wav"

# use text to speech to notify about a given text
def notify(text):
	if not settings["enabled"]: return
	command = "pico2wave -w "+filename+" '"+text+"' && aplay "+filename
	utils.run_command(command)

# main
if __name__ == '__main__':
	if len(sys.argv) != 2:
		print "Usage: notification_audio.py <text>"
	else:
		notify(sys.argv[1])
