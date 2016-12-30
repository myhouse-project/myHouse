#!/usr/bin/python
import sys
import subprocess
import os

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
	devnull = open("/dev/null","w")
	subprocess.call(["pico2wave", "-l",settings["language"],"-w",filename, text],stderr=devnull)
	subprocess.call(["aplay", filename],stderr=devnull)
	os.remove(filename)

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: notification_audio.py <text>"
	else:
		notify(sys.argv[1])
