#!/usr/bin/python
import sys
import serial
from curses import ascii

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["gsm_sms"]

# send a sms with the given text
def notify(text):
	text = "["+conf["general"]["house_name"]+"] "+text
	# truncate the text
	text = (data[:150] + '..') if len(text) > 150 else text
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
		        # switch to text mode
		        modem.write(b'AT+CMGF=1\r')
			# set the recipient number
			modem.write(b'AT+CMGS="' + to.encode() + b'"\r')
			# send the message
			modem.write(text.encode())
			# end the message with ctrl+z
			modem.write(ascii.ctrl('z'))
			log.info("Sent SMS to "+str(to)+" with text: "+text)
		except Exception,e:
			log.error("Failed to send SMS to "+str(to)+": "+utils.get_exception(e))
	# disconect
	modem.close()

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: "+__file__+" <text>"
	else:
		notify(sys.argv[1])
