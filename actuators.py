#!/usr/bin/python
import sys
import os
import datetime
import json
import time
import copy

import utils
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()

import actuator_messagebridge

# variables
push_plugins = {}

# return the appropriate plugin
def get_plugin(name):
	plugin = None
	if name == "messagebridge": plugin = actuator_messagebridge
	return plugin

# initialize an actuator data structure
def init_actuator(actuator,module_id):
	actuator = copy.deepcopy(actuator)
        # add module if not there yet
        actuator['module_id'] = module_id
        # determine the plugin to use
        actuator["plugin_module"] = get_plugin(actuator["plugin"]["name"])
        if actuator["plugin_module"] is None:
                log.error("["+module_id+"]["+actuator_id+"] plugin "+actuator["plugin"]["name"]+" not supported")
                return None
	return actuator

# run an action with the actuator
def run(module_id,actuator_id,message):
	# ensure the actuator exist
	actuator = utils.get_actuator(module_id,actuator_id)
	actuator = init_actuator(actuator,module_id)
	if actuator is None: 
		log.error("["+module_id+"]["+actuator_id+"] not found, skipping it")
		return
	# send the message
	log.debug("["+actuator["module_id"]+"]["+actuator["actuator_id"]+"] sending message "+message)
	actuator["plugin_module"].send(actuator,message)

# initialize configured push plugins
def init_push_plugins():
        # for each push plugin
        for plugin_name,plugin_conf in conf["plugins"]["actuators"].iteritems():
                # skip other plugins
                if plugin_conf["type"] != "push": continue
                # get the plugin and store it
                plugin_module = get_plugin(plugin_name)
                if plugin_module is None:
                        log.error("push plugin "+plugin_name+" not supported")
                        continue
                push_plugins[plugin_name] = plugin_module
                # start the plugin
                log.info("starting push plugin "+plugin_name)
		schedule.add_job(plugin_module.run,'date',run_date=datetime.datetime.now())

# schedule each actuator
def schedule_all():
	# init push plugins
	init_push_plugins()
	log.info("initializing actuators")
        # for each module
        for module in conf["modules"]:
		if not module["enabled"]: continue
		# skip modules without actuators
		if "actuators" not in module: continue
		for actuator in module["actuators"]:
			# initialize the actuator
			actuator = init_actuator(actuator,module['module_id'])
			if actuator is None: continue
			# skip actuators wihtout a plugin
			if 'plugin' not in actuator: continue
			if actuator['plugin']['name'] not in conf['plugins']['actuators']:
				log.error("["+actuator['module_id']+"]["+actuator['actuator_id']+"] invalid plugin "+actuator['plugin']['name'])
				continue
			# handle push plugins
			if conf['plugins']['actuators'][actuator['plugin']['name']]['type'] != "push": continue
			# register the actuator
			log.debug("["+actuator['module_id']+"]["+actuator['actuator_id']+"] registering with push service "+actuator['plugin']['name'])
			push_plugins[actuator['plugin']['name']].register_actuator(actuator)

# allow running it both as a module and when called directly
if __name__ == '__main__':
	if len(sys.argv) != 4: 
		# no arguments provided, schedule all actuators
		schedule.start()
		schedule_all()
	        while True:
	                time.sleep(1)
	else: 
		# run the command for the given actuator
		# <module_id> <actuator_id> <action>
		run(sys.argv[1],sys.argv[2],sys.argv[3])

