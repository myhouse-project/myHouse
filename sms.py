#!/usr/bin/python
import sys

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["sms"]
max_retries = 5
timeout = 30

# send a sms with the given text
def notify(text):
	text = "["+conf["general"]["house_name"]+"] "+text
	for to in settings["to"]:
		retries = max_retries
		while retries > 0 :
			result = send(to,text)
			if result: 
				log.info("Sent SMS to "+str(to)+" with text: "+text)
				retries = 0
		        else: 
				log.error("Failed #"+str(retries)+" to send SMS to "+str(to)+" with text: "+text)
				retries = retries - 1

# send the message
def send(to,text):
	protocol = "https://" if settings["ssl"] else "http://"
	url = protocol+settings["hostname"]+"/myaccount/sendsms.php?username="+settings["username"]+"&password="+settings["password"]+"&from="+str(settings["from"])+"&to="+str(to)+"&text="+text
	try: 
		response = utils.web_get(url,timeout=timeout)
	except Exception,e:
		log.warning("unable to connect to the sms service: "+utils.get_exception(e))
		return False
	if "<resultstring>success</resultstring>" in response: return True
	return False

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: "+__file__+" <text>"
	else:
		notify(sys.argv[1])
