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
wait = "%wait%"
cleanup = re.compile('[^a-zA-Z ]')

# load the oracle's basic knowledge
def load_brain():
	global not_understood
	global prefix
	global wait
	with open(conf["constants"]["bot_brain_file"], 'r') as file:
        	for line in file:
			request,response  = line.rstrip().split("=>")
			request = request.lower()
			response = response.lower()
			# load default messages
			if request == not_understood: not_understood = "text|"+response
			if request == prefix: prefix = response.split("|")
			if request == wait: wait = response.split("|")
			# populate the knowledge base
			else: kb[request] = "text|"+response

# enrich the knowledge base with the configuration
def learn_config():
	r = {}
        for module in conf["modules"]:
		r["module"] = [module["module_id"],module["display_name"]]
		if "rules" in module:
			for rule in module["rules"]:
				if not rule["enabled"]: continue
				if len(rule["conditions"]) != 0: continue
				r["rule"] = copy.deepcopy(r["module"])
				r["rule"].extend([rule["rule_id"],rule["display_name"]])
				context = module["module_id"]+"|"+rule["rule_id"]
				# user requesting for an alert
				kb[cleanup.sub(' '," ".join(r["rule"])).lower()] = "rule|"+context
		if "widgets" in module:
			for i in range(len(module["widgets"])):
				for j in range(len(module["widgets"][i])):
					widget = module["widgets"][i][j]
					for k in range(len(widget["layout"])):
						layout = widget["layout"][k]
						# ignore if not an image, a chart or a sensor timeline
						if layout["type"] != "image" and layout["type"] != "map" and not layout["type"].startswith("chart_") and not layout["type"].startswith("sensor_"): continue
	                			r["layout"] = copy.deepcopy(r["module"])
			                        r["layout"].extend(["chart","widget",widget["widget_id"],widget["display_name"],layout["type"]])
						context = module["module_id"]+"|"+widget["widget_id"]
						# user requesting for a widget
						kb[cleanup.sub(' '," ".join(r["layout"])).lower()] = "chart|"+context
					
# initialize the oracle		
def init():
        if initialized: return
	# load basic knowledge
	load_brain()
	# learn from the configuration
	learn_config()

# add a random prefix
def add_prefix(text):
	add_prefix_rnd = utils.randint(0,100)
	if add_prefix_rnd < 50:
		return prefix[utils.randint(0,len(prefix)-1)]+" "+text[0].lower() + text[1:]
	return text

# return a random wait message
def get_wait_message():
	return wait[utils.randint(0,len(wait)-1)]	

# translate the action to take in a human readable response
def translate_response(action):
	response = {'type':'text', 'content': ''}
	request = action.split("|")
	what = request.pop(0)
	if what == "text":
		response["content"] = request[utils.randint(0,len(request)-1)]
	elif what == "rule":
		response["content"] = add_prefix(alerter.run(request[0],request[1],notify=False))
	elif what == "chart":
		response["type"] = "chart"
		response["content"] = request[0]+","+request[1]
	return response
	
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
	# send it back
	log.info("I am "+str(score)+"% sure so I would respond with: "+str(response))
	return response

# main
if __name__ == '__main__':
        if len(sys.argv) != 2:
		print 'Usage: oracle.py "sentence for the oracle"'
	else:
		ask(sys.argv[1])
