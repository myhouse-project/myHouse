#!/usr/bin/python
import sys
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import copy
import re

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import alerter

# variables
# kb format: words => action
kb = {}
initialized = False
# possible values: fuzz.ratio, fuzz.partial_ratio, fuzz.token_sort_ratio, fuzz.token_set_ratio
scorer = fuzz.token_set_ratio
not_understood = "%not_understood%"
not_understood_score = 50
prefix = "%prefix%"
cleanup = re.compile('[^a-zA-Z ]')

# load the oracle's basic knowledge
def load_brain():
	global not_understood
	global prefix
	with open(conf["constants"]["bot_brain_file"], 'r') as file:
        	for line in file:
			request,response  = line.rstrip().split("=>")
			request = request.lower()
			response = response.lower()
			# load default messages
			if request == not_understood: not_understood = "text|"+response
			if request == prefix: prefix = "text|"+response
			# populate the knowledge base
			else: kb[request] = "text|"+response

# enrich the knowledge base with the configuration
def learn_config():
	r = {}
        for module in conf["modules"]:
		r["module"] = [module["module_id"],module["display_name"]]
		if "alerts" in module:
			for alert in module["alerts"]:
				if len(alert["conditions"]) != 0: continue
				r["alert"] = copy.deepcopy(r["module"])
				r["alert"].extend([alert["alert_id"],alert["display_name"]])
				context = module["module_id"]+"|"+alert["alert_id"]
				# user requesting for an alert
				kb[cleanup.sub(' '," ".join(r["alert"])).lower()] = "alert|"+context
	
# initialize the oracle		
def init():
        if initialized: return
	# load basic knowledge
	load_brain()
	# learn from the configuration
	learn_config()

# translate the action to take in a human readable response
def translate_response(action):
	response = action.split("|")
	what = response.pop(0)
	if what == "text":
		return response[utils.randint(0,len(response)-1)]
	if what == "alert":
		return alerter.run(response[0],response[1],False)		
	
# ask the oracle a question
def ask(request):
	init()
	request = cleanup.sub(' ',request)
	log.info("I've been asked: "+request)
	# identify the most suitable action to take
	match, score = process.extractOne(request,kb.keys(),scorer=scorer)
	action = kb[match]
	log.debug("I would take this action: "+action)
	# ensure the score is high enough to provide a confident answer
	if score < not_understood_score: action = not_understood
	# translate the action into a response
	response = translate_response(action)
	# add some randomness in the response
	if not action.startswith("text|"):
		add_prefix = utils.randint(0,100)
		if add_prefix < 50: 
			response = translate_response(prefix)+" "+response[0].lower() + response[1:]
	# send it back
	log.info("I am "+str(score)+"% sure to responde with: "+response)
	return response

# main
if __name__ == '__main__':
        if len(sys.argv) != 2:
		print 'Usage: oracle.py "sentence for the oracle"'
	else:
		ask(sys.argv[1])
