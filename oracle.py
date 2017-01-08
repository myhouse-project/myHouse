#!/usr/bin/python
import sys
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
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
# define the scorer to use
if conf["input"]["settings"]["algorithm"] == "ratio": scorer = fuzz.ratio
elif conf["input"]["settings"]["algorithm"] == "partial_ratio": scorer = fuzz.partial_ratio
elif conf["input"]["settings"]["algorithm"] == "token_sort_ratio": scorer = fuzz.token_sort_ratio
elif conf["input"]["settings"]["algorithm"] == "token_set_ratio": scorer = fuzz.token_set_ratio
# define the minimum score 
not_understood_score = conf["input"]["settings"]["score"]
# othre variables
not_understood = "%not_understood%"
prefix = "%prefix%"
wait = "%wait%"
cleanup = re.compile('[^a-zA-Z ]')

# load the oracle's basic knowledge
def load_brain():
	global not_understood
	global prefix
	global wait
	filename = conf["constants"]["bot_brain_file"]+"_"+conf["general"]["language"]+".dict"
	with open(filename, 'r') as file:
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
def learn_config(include_widgets):
	r = {}
	widgets = []
	for module in conf["modules"]:
		if "rules" in module:
			for rule in module["rules"]:
				if not rule["enabled"]: continue
				# ignore rules with a condition
				if len(rule["conditions"]) != 0: continue
				# keywords are the rule display name and additional keywords if any
				keywords = utils.lang(rule["display_name"])
				if "keywords" in rule: keywords = keywords+" "+rule["keywords"]
				# user requesting for an alert
				kb[cleanup.sub(' ',keywords).lower()] = "rule|"+module["module_id"]+"|"+rule["rule_id"]
		if "widgets" in module and include_widgets:
			for i in range(len(module["widgets"])):
				for j in range(len(module["widgets"][i])):
					widget = module["widgets"][i][j]
					if widget["widget_id"] in widgets:
						# perform a sanity check on the widget_id
						log.warning("Duplicated widget "+widget["widget_id"]+" found. Widgets must have a unique name across all the modules")
					widgets.append(widget["widget_id"])
					for k in range(len(widget["layout"])):
						layout = widget["layout"][k]
						# consider only the layouts we can generate a chart of
						if layout["type"] == "image" or layout["type"] == "map" or layout["type"].startswith("chart_") or layout["type"].startswith("sensor_"):
							keywords = utils.lang(widget["display_name"])
							if "keywords" in rule: keywords = keywords+" "+rule["keywords"]
							# user requesting for a widget
							kb[cleanup.sub(' ',keywords).lower()] = "chart|"+module["module_id"]+"|"+widget["widget_id"]
							break
					
# initialize the oracle		
def init(include_widgets=True):
	if initialized: return kb
	# load basic knowledge
	load_brain()
	# learn from the configuration
	learn_config(include_widgets)
	return kb

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
def ask(request,custom_kb=None):
	# determine which kb to use
	if custom_kb is not None: current_kb = custom_kb
	else: current_kb = init()
	# clean up the request
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
		print 'Usage: '+__file__+' "sentence for the oracle"'
	else:
		ask(sys.argv[1])
