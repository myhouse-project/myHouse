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
settings = conf["output"]["gsm_sms"]
timeout = 30

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
			i = timeout
			done = False
			while True:
				# send the sms
				if i == 30: send_sms(modem,to,text)
				# read the output
				output = modem.readlines()
				for line in output:
                                        line = str(line).rstrip()
                                        if line == "": continue
                                        log.debug("Modem output: "+line)
					if "+CMGS:" in line:
						log.info("Sent SMS to "+str(to)+" with text: "+text)
						done = True
                                        if "ERROR" in line:
                                                done = True
                                                break
				if done: break
				i = i - 1
				if i == 0:
					# timeout reached
					log.error("Unable to send SMS to "+str(to)+": timeout reached")
					break
		except Exception,e:
			log.error("Failed to send SMS to "+str(to)+": "+utils.get_exception(e))
	# disconect
	modem.close()

# send a sms message
def send_sms(modem,to,text):
	log.debug("Sending SMS "+str(to))
	time.sleep(2)
        # switch to text mode
        modem.write(b'AT+CMGF=1\r')
        time.sleep(2)
        # set the recipient number
        modem.write(b'AT+CMGS="' + to.encode() + b'"\r')
        time.sleep(2)
        # send the message
        modem.write(text.encode())
        time.sleep(1)
        # end the message with ctrl+z
        modem.write(ascii.ctrl('z'))

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: "+__file__+" <text>"
	else:
		notify(sys.argv[1])
