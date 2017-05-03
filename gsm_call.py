#!/usr/bin/python
import sys
import serial
import time
from curses import ascii

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["gsm_call"]
timeout = 50

# send a sms with the given text
def notify(text):
	# connect to the modem
	try:
		log.debug("Connecting to GSM modem on port "+settings["port"]+" with baud rate "+str(settings["baud"]))
		modem = serial.Serial(settings["port"],settings["baud"], timeout=0.5)
	except Exception,e:
        	log.error("Unable to connect to the GSM modem: "+utils.get_exception(e))
                return
	# for each recipient
	for to in settings["to"]:
		try: 
			i = timeout
			done = False
			while True:
				# place the call
				if i == 30: make_call(modem,to,settings["duration"])
				# read the output
				output = modem.readlines()
				for line in output:
					log.info("Modem output: "+str(line).rstrip())
					if '"SOUNDER",0' in line:
						log.info("Called "+str(to))
						done = True
				if done: break
				i = i - 1
				if i == 0:
					# timeout reached
					log.error("Unable to call "+str(to)+": timeout reached")
					break
		except Exception,e:
			log.error("Failed to call "+str(to)+": "+utils.get_exception(e))
	# disconect
	modem.close()

# make a call
def make_call(modem,to,duration):
	time.sleep(2)
        # place the call
	modem.write(b'ATD+'+to+'\r')
	# make the phone ring for the configured tie
        time.sleep(duration)
	# hung up 
	modem.write(b'ATH\r')

# main
if __name__ == '__main__':
	notify("")
