#!/usr/bin/python
import sys

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["sms"]

# send a sms with the given text
def notify(text):
	text = "["+conf["general"]["house_name"]+"] "+text
	for to in settings["to"]:
		protocol = "https://" if settings["ssl"] else "http://"
		url = protocol+settings["hostname"]+"/myaccount/sendsms.php?username="+settings["username"]+"&password="+settings["password"]+"&from="+str(settings["from"])+"&to="+str(to)+"&text="+text
		response = utils.web_get(url)
		if "<resultstring>success</resultstring>" in response:
			log.info("Sent SMS to "+str(to)+" with text: "+text)
		else:
			log.error("Failed to send SMS to "+str(to)+" with text: "+text)

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print "Usage: "+__file__+" <text>"
	else:
		notify(sys.argv[1])
