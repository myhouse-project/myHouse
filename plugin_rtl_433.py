#!/usr/bin/python
import datetime
import json
import time
import json
import subprocess
import shlex

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import sensors

# nodes[<search>][<measure>] = sensor
# e.g. nodes["{'model':'THGR122N','id':134}"]["temperature_C"]
nodes = {}
plugin_conf = conf['plugins']['rtl_433']
default_measure = "__measure__"
default_value = 1
command_arguments = "-F json -U"

# register a new sensor against this plugin
def register(sensor):
	if sensor['plugin']['plugin_name'] != 'rtl_433': return
	# create a data structure for each search string
	search_string = json.dumps(sensor['plugin']['search'])
	if search_string not in nodes: nodes[search_string] = {}
	# if no measures are provided, set it to the default_measure
	if "measure" not in sensor['plugin']: sensor['plugin']['measure'] = default_measure
	measure = sensor['plugin']['measure']
	# check if the measure has already been registered
	if measure in nodes[search_string]:
		log.warning("["+__name__+"]["+search_string+"]["+measure+"] already registered, skipping")
		return
	# create a data structure for each measure of each search_string
	nodes[search_string][measure] = {}
	# add the sensor to the nodes list
	nodes[search_string][measure] = sensor
	log.debug("["+__name__+"]["+search_string+"]["+measure+"] registered sensor "+sensor['module_id']+":"+sensor['group_id']+":"+sensor['sensor_id'])

# run the plugin service
def run():
	if not plugin_conf["enabled"]: return
	# kill rtl_433 if running
	utils.run_command("killall rtl_433")
	# run rtl_433 and handle the output
	command = plugin_conf['command']+" "+command_arguments
	log.debug("["+__name__+"] running command "+command)
	process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	prev_output = ""
	while True:
		# read a line from the output
		output = process.stdout.readline()
		if output == '' and process.poll() is not None:
			# process ended, break
			log.info("["+__name__+"] rtl_433 has ended")
			break
		if output:
			# output available
			try:
	                        # avoid handling the same exact output, skipping
	                        if prev_output == output: continue
				# parse the json output
				json_output = json.loads(output)
                        except ValueError, e:
                                # not a valid json, ignoring
                                continue
			# for each registered search string
			for search_string in nodes:
				# check if the output matches the search string
				search_json = json.loads(search_string)
				found = True
				for key, value in search_json.iteritems():
					# check every key/value pair
					if key not in json_output: found = False
					if str(value) != str(json_output[key]): found = False
				if not found: continue
				# found, save each measure
				node = nodes[search_string]
				measures = []
				for measure in node:
					sensor = node[measure]
					# create the measure data structure
					measure_data = {}
					if "time" in json_output:
						date = datetime.datetime.strptime(json_output["time"],"%Y-%m-%d %H:%M:%S")
						measure_data["timestamp"] = utils.timezone(utils.timezone(int(time.mktime(date.timetuple()))))
					measure_data["key"] = sensor["sensor_id"]
					value = json_output[measure] if measure in json_output else default_value
					measure_data["value"] = utils.normalize(value,conf["constants"]["formats"][sensor["format"]]["formatter"])
					measures.append(measure_data)
					sensors.store(sensor,measures)
			# keep track of the last line of output
			prev_output = output
