#!/usr/bin/python

import logging
import os
import sys
import json
from collections import OrderedDict
import copy
import subprocess

import config
conf = config.get_config(validate=False)
import utils
import db

db_file = conf["db"]["database_file"]
debug = False
log = logging.getLogger("upgrade")
base_dir = os.path.abspath(os.path.dirname(__file__))
log_file = base_dir+"/logs/upgrade.log"

# initialize the logger
def init_logger():
        log.setLevel(logging.DEBUG)
        # initialize console logging
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        log.addHandler(console)
        # initialize file logging
        file = logging.FileHandler(log_file)
        file.setLevel(logging.DEBUG)
        file.setFormatter(logging.Formatter('[%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s',"%Y-%m-%d %H:%M:%S"))
        log.addHandler(file)

# change into a given database number
def change_db(database):
	db.db = None
	conf['db']['database'] = database

# run a command and return the output
def run_command(command,return_code=False):
        log.debug("Executing "+command)
        # run the command and buffer the output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        for line in process.stdout.readlines(): output = output+line
        log.debug(output.rstrip())
        # return the output or the return code
        ret = process.poll()
        if return_code: return ret
        else:
                if ret != 0: log.info("WARNING: during the execution of "+command+": "+output)
                return output

# backup the database and the configuration file
def backup(version):
	if not utils.file_exists(db_file): 
		log.info("ERROR: unable to find the database at "+db_file)
		exit()
	backup_db_file = conf["constants"]["tmp_dir"]+"/dump.rdb_"+str(version)
	log.info("Backing up the database "+db_file+" into "+backup_db_file)
	run_command("cp -f "+db_file+" "+backup_db_file)
	if utils.file_exists(conf["constants"]["config_file"]):
		backup_config_file = conf["constants"]["tmp_dir"]+"/config.json_"+str(version)
		log.info("Backing up the configuration file "+conf["constants"]["config_file"]+" into "+backup_config_file)
		run_command("cp -f "+conf["constants"]["config_file"]+" "+backup_config_file)

# upgrade from 1.x to 2.0
def upgrade_2_0():
	######## START OF CONFIGURATION
	# remote all data from the target database
	empty_target_db = False
	# migrate history data
	migrate_history = True
	# history start timestamp to migrate, "-inf" for all
	history_start_timestamp = "-inf"
	# historu end timestamp to migrate
	history_end_timestamp = utils.now()
	# migrate recent data
	migrate_recent = True
	# database number from which we are migrating
	db_from = 1
	# database number into which we are migrating
	db_to = 2
	# debug
	debug = False
	# keys to migrate history (from key -> to key)
	# destination key format: myHouse:<module_id>:<group_id>:<sensor_id>
	history = {
		'home:weather:outdoor:temperature:day:max': 'myHouse:outdoor:temperature:external:day:max',
		'home:weather:outdoor:temperature:day:min': 'myHouse:outdoor:temperature:external:day:min',
		'home:weather:outdoor:temperature:day': 'myHouse:outdoor:temperature:external:day:avg',
	
		'home:weather:indoor:temperature:day:max': 'myHouse:indoor:temperature:living_room:day:max',
		'home:weather:indoor:temperature:day:min': 'myHouse:indoor:temperature:living_room:day:min',
		'home:weather:indoor:temperature:day': 'myHouse:indoor:temperature:living_room:day:avg',
	
		'home:weather:almanac:record:min': 'myHouse:outdoor:temperature:record:day:min',
		'home:weather:almanac:record:max': 'myHouse:outdoor:temperature:record:day:max',
	
		'home:weather:almanac:normal:min': 'myHouse:outdoor:temperature:normal:day:min',
		'home:weather:almanac:normal:max': 'myHouse:outdoor:temperature:normal:day:max',
	
		'home:weather:outdoor:condition:day': 'myHouse:outdoor:temperature:condition:day:avg',
	}
	# keys to migrate recent data (from key -> to key)
	recent = {
		'home:weather:outdoor:temperature:measure': 'myHouse:outdoor:temperature:external',
		'home:weather:indoor:temperature:measure': 'myHouse:indoor:temperature:living_room',
		'home:weather:outdoor:condition:measure': 'myHouse:outdoor:temperature:condition',
	}
	######## END OF CONFIGURATION
	conf = config.get_config(validate=False)
	print "[Migration from v1.x to v2.0]\n"
	input("WARNING: which data will be migrate is defined within this script, on top of the upgrade_20() function.\nIndividual sensors to migrate must be specified manually\nPlase ensure you have reviewed all the settings first!\n\nPress Enter to continue...")
	backup("1.0")
	# empty the target database first
	if empty_target_db:
		print "Flushing target database..."
		change_db(db_to)
		db.flushdb()
	# for each history key to migrate
	print "Migrating historical data..."
	for key_from in history:
		if not migrate_history: break
		key_to = history[key_from]
		print "\tMigrating "+key_from+" -> "+key_to
		# retrieve all the data
		change_db(db_from)
		data = db.rangebyscore(key_from,history_start_timestamp,history_end_timestamp,withscores=True)
		change_db(db_to)
		count = 0
		# for each entry
		for entry in data:
			timestamp = utils.day_start(utils.timezone(entry[0]))
			value = utils.normalize(entry[1])
			# store it into the new database
			if debug: print "[HISTORY]["+key_to+"] ("+utils.timestamp2date(timestamp)+") "+str(value)
			db.set(key_to,value,timestamp)
			count = count +1
		print "\t\tdone, "+str(count)+" values"
	# for each recent key to migrate
	print "Migrating recent data..."
	for key_from in recent:
		if not migrate_recent: break
		key_to = recent[key_from]
		print "\tMigrating "+key_from+" -> "+key_to
		# retrieve the recent data
		change_db(db_from)
		data = db.rangebyscore(key_from,utils.now()-2*conf["constants"]["1_day"],utils.now(),withscores=True)
		change_db(db_to)
		count = 0
		# for each entry
		for entry in data:
			timestamp = utils.timezone(entry[0])
			value = utils.normalize(entry[1])
			if debug: print "[RECENT]["+key_to+"] ("+utils.timestamp2date(timestamp)+") "+str(value)
			# skip it if the same value is already stored
			old = db.rangebyscore(key_to,timestamp,timestamp)
			if len(old) > 0: continue
			# store it into the new database
			db.set(key_to,value,timestamp)
			# create the sensor data structure
			key_split = key_to.split(":")
			group_id = key_split[-2]
			sensor_id = key_split[-1]
			module_id = key_split[-4]
			sensor = utils.get_sensor(module_id,group_id,sensor_id)
			sensor['module_id'] = module_id
			sensor['group_id'] = group_id
			sensor['db_group'] = conf["constants"]["db_schema"]["root"]+":"+sensor["module_id"]+":"+sensor["group_id"]
			sensor['db_sensor'] = sensor['db_group']+":"+sensor["sensor_id"]
			import sensors
			sensors.summarize(sensor,'hour',utils.hour_start(timestamp),utils.hour_end(timestamp))
			count = count +1
		print "\t\tdone, "+str(count)+" values"
	print "Upgrading database..."
	version_key = conf["constants"]["db_schema"]["version"]
	db.set_simple(version_key,"2.0")


# upgrade from 2.0 to 2.1
def upgrade_2_1():
	# CONFIGURATION
	upgrade_db = True
	upgrade_conf = True
	upgrade_service = False
	# END
	conf = config.get_config(validate=False)
	print "[Migration from v2.0 to v2.1]\n"
	backup("2.0")
	if upgrade_db:
		print "Upgrading database..."
		version_key = conf["constants"]["db_schema"]["version"]
		db.set_simple(version_key,"2.1")
	if upgrade_conf:
		print "Upgrading configuration file..."
		new = json.loads(conf["config_json"], object_pairs_hook=OrderedDict)
		# upgrade logging
		new["logging"]["rotate_size_mb"] = 5
		new["logging"]["rotate_count"] = 5
		# upgrade sensors
		new["sensors"]["poll_at_startup"] = True
		new["sensors"]["data_expire_days"] = 5
		new["sensors"]["cache_expire_min"] = 1
		# upgrade gui
		new["gui"]["maps"] = {}
		new["gui"]["maps"]["type"] = "hybrid"
		new["gui"]["maps"]["size_x"] = 640
		new["gui"]["maps"]["size_y"] = 640
		new["gui"]["maps"]["api_key"] = "YOUR_API_KEY"
		# upgrade alerter
		new["alerter"]["data_expire_days"] = 5
		# upgrade plugins
		new["plugins"]["messagebridge"]["enabled"] = False
		new["plugins"]["rtl_433"] = {}
		new["plugins"]["rtl_433"]["enabled"] = False
		new["plugins"]["rtl_433"]["command"] = "/usr/local/bin/rtl_433"
		new["plugins"]["gpio"] = {}
		new["plugins"]["gpio"]["enabled"] = False
		new["plugins"]["gpio"]["mode"] = "bcm"
		# upgrade modules
		migrate_icloud = []
		for module in new["modules"]:
			if "widgets" in module:
				for i in range(len(module["widgets"])):
					for j in range(len(module["widgets"][i])):
						widget = module["widgets"][i][j]
						for k in range(len(widget["layout"])):
							layout = widget["layout"][k]
							if layout["type"] == "checkbox" and "url" in layout:
								# migrade "url" in send_on/send_off for checkbox
								layout["send_on"] = layout["url"]+"1"
								layout["send_off"] = layout["url"]+"0"
								del layout["url"]
			if "sensors" in module:
				for i in range(len(module["sensors"])):
					sensor = module["sensors"][i]
					if "plugin" in sensor and sensor["plugin"]["plugin_name"] == "icloud":
						# convert from image to string the icloud sensor format
						sensor["format"] = "string"
						if "single_instance" in sensor: del sensor["single_instance"]
						migrate_icloud.append(module["module_id"]+":"+sensor["group_id"]+":"+sensor["sensor_id"])
		for module in new["modules"]:
			if "widgets" in module:
				for i in range(len(module["widgets"])):
					for j in range(len(module["widgets"][i])):
						widget = module["widgets"][i][j]
						for k in range(len(widget["layout"])):
							layout = widget["layout"][k]
							if layout["type"] == "image" and sensor in migrate_icloud:
								layout["type"] = "map"
		# save the updated configuration 
		config.save(json.dumps(new, default=lambda o: o.__dict__))
	if upgrade_service:
		print "Upgrading init script..."
		# rename main.py in myHouse.py in the init script
		filedata = None
		with open(conf['constants']['service_location'], 'r') as file :
			filedata = file.read()
		filedata = filedata.replace("main.py","myHouse.py")
		with open(conf['constants']['service_location'], 'w') as file:
			file.write(filedata)
		# delete the old main.py
		utils.run_command("rm -f "+conf["constants"]["base_dir"]+"/main.py")

# upgrade from 2.1 to 2.2
def upgrade_2_2():
	# CONFIGURATION
	upgrade_conf = True
	upgrade_db = True
	# END
	conf = config.get_config(validate=False)
	print "[Migration from v2.1 to v2.2]\n"
	backup("2.1")
	if upgrade_conf:
		print "Upgrading configuration file..."
		new = json.loads(conf["config_json"], object_pairs_hook=OrderedDict)
		# delete the linux plugin
		del new["plugins"]["linux"]
		# add the command plugin
		new["plugins"]["command"] = {}
		new["plugins"]["command"]["timeout"] = 30
		# add the system plugin
		new["plugins"]["system"] = {}
		new["plugins"]["system"]["timeout"] = 30
		# add timeout to image
		new["plugins"]["image"] = {}
		new["plugins"]["image"]["timeout"] = 30
		# add the earthquake plugin
		new["plugins"]["earthquake"] = None
		# add the rss plugin
		new["plugins"]["rss"] = None
		# add the mqtt plugin
		new["plugins"]["mqtt"] = {}
		new["plugins"]["mqtt"]["enabled"] = False
		new["plugins"]["mqtt"]["hostname"] = "localhost"
		new["plugins"]["mqtt"]["port"] = 1883
		# add the ds18b20 plugin
		new["plugins"]["ds18b20"] = None
		# add the dht plugin
		new["plugins"]["dht"] = None
		# add additional options in db
		new["db"]["database_file"] = "/var/lib/redis/dump.rdb"
		new["db"]["backup"] = {}
		new["db"]["backup"]["daily"] = True
		new["db"]["backup"]["weekly"] = True
		# add the ads1x15 plugin
		new["plugins"]["ads1x15"] = None
		print "\tINFO: please be aware the following new plugins are now available: earthquake, mqtt, ds18b20, dht, ads1x15, rss. Review the documentation for details"
		# add general
		new["general"] = {}
		new["general"]["latitude"] = 0
		new["general"]["longitude"] = 0
		new["general"]["house_name"] = "myHouse"
		print "\tWARNING: different plugins use now the new 'latitude' and 'longitude' settings in 'general', ensure they are correct"
		# add language
		new["general"]["language"] = "en"
		print "\tINFO: multiple languages are now supported. Define your language in 'general' and create your aliases for each 'display_name' variable"
		# move units and timeframe under general
		new["general"]["units"] = conf["units"]
		del new["units"]
		new["general"]["timeframes"] = conf["timeframes"]
		del new["timeframes"]
		# migrate sections
		new_sections = []
		for section in new["gui"]["sections"]: 
			section_item = {}
			section_item["section_id"] = section
			section_item["display_name"] = {}
			section_item["display_name"]["en"] = section
			new_sections.append(section_item)
		new["gui"]["sections"] = new_sections
		# define the news module
		news = {
		      "module_id": "news",
		      "section_id": "Main",
		      "display_name": {
		                "en": "News"
	                },
		      "icon": "fa-newspaper-o",
		      "enabled": True,
		      "widgets": [
		        [
		          {
		            "widget_id": "news_recent",
		            "display_name": {
	                                "en": "Recent News"
                                },
		            "enabled": True,
		            "size": 12,
		            "layout": [
		              {
		                "type": "table",
		                "sensor": "news:rss:all_news",
		                "columns": ""
		              }
		            ]
		          }
		        ]
		      ],
		      "sensors": [
		        {
                	  "module_id": "news",
		          "group_id": "rss",
		          "sensor_id": "all_news",
	                  "enabled": True,
		          "plugin": {
		            "plugin_name": "rss",
		            "url": "http://rss.cnn.com/rss/edition.rss",
	                    "polling_interval": 20
		          },
		          "format": "string",
	                  "retention": {
	                        "realtime_count": 1
	                  }
		        }
		      ]
		}
		# define the power module
		power =  {
		      "module_id": "power",
		      "section_id": "System",
		      "display_name": {
			"en": "Reboot/Shutdown",
			},
		      "icon": "fa-power-off",
		      "enabled": True,
		      "widgets": [
			[
			  {
			    "widget_id": "reboot",
			    "display_name": {
				"en": "Reboot the system",
			     },
			    "enabled": True,
			    "size": 4,
			    "offset": 1,
			    "layout": [
			      {
				"type": "button",
				"display_name": {
					"en": "Reboot",
				},
				"send": "power/command/reboot/run/save"
			      }
			    ]
			  },
			  {
			    "widget_id": "shutdown",
			    "display_name": {
				"en": "Shutdown the system",
			    },
			    "enabled": True,
			    "size": 4,
			    "offset": 2,
			    "layout": [
			      {
				"type": "button",
				"display_name": {
					"en": "Shutdown",
				},
				"send": "power/command/shutdown/run/save"
			      }
			    ]
			  }
			]
		      ],
			"sensors": [
			{
			  "module_id": "power",
			  "group_id": "command",
			  "sensor_id": "reboot",
			  "enabled": True,
			  "plugin": {
			    "plugin_name": "system",
			    "measure": "reboot"
			  },
			  "format": "string",
			  "retention": {
				"realtime_count": 1
			  }
			},
			{
			  "module_id": "power",
			  "group_id": "command",
			  "sensor_id": "shutdown",
   	                  "enabled": True,
			  "plugin": {
			    "plugin_name": "system",
			    "measure": "shutdown"
			  },
			  "format": "string",
			  "retention": {
				"realtime_count": 1
			  }
			}
		      ]
		}
		# add retention to sensors
		new["sensors"]["retention"] = {}
		new["sensors"]["retention"]["realtime_new_only"] = False
		new["sensors"]["retention"]["realtime_count"] = 0
		new["sensors"]["retention"]["realtime_days"] = 5
		new["sensors"]["retention"]["recent_days"] = 5
		new["sensors"]["retention"]["history_days"] = 0
		# add language to weatherchannel
		new["plugins"]["weatherchannel"]["language"] = "en"
		# delete location from weatherchannel and wunderground
		del new["plugins"]["weatherchannel"]["location"]
		del new["plugins"]["wunderground"]["location"]
		print "\tWARNING: 'location' in 'plugins/wunderground' and 'plugins/weatherchannel' has been precated, use the new 'latitude' and 'longitude' in 'general' instead"
		# delete csv_file from the csv plugin
		if "csv_file" in new["plugins"]["csv"]:
			print "\tWARNING: 'csv_file' in 'plugins/csv' has been deprecated, specify the filename in each sensor"
		new["plugins"]["csv"] = None
		# warn about data_expire_days
		print "\tWARNING: data_expire_days in 'sensors' has been deprecated, use 'retention' instead"
		del new["sensors"]["data_expire_days"]
		# warn about icloud widget
		print "\tWARNING: if you have any widget displaying the position of an icloud-based sensor, please manually edit it. Set 'type' to 'map', 'group' to the group of sensors, 'tracking' to 'true' and 'timeframe' to 'realtime'"
		# add output
		new["output"] = {}
		# migrate notifications into output
		new["output"]["email"] = conf["notifications"]["email"]
		new["output"]["slack"] = conf["notifications"]["slack"]
		# add email subject
		new["output"]["email"]["subject"] = "Notification"
		del new["notifications"]
		# add sms notification
		sms =  {
			"enabled": False,
			"ssl": False,
			"hostname": "www.freevoipdeal.com",
			"username": "",
			"password": "",
			"from": "",
			"to": [   ],
			"min_severity": "alert",
			"rate_limit": 1
		}
		new["output"]["sms"] = sms
		# add audio notification
		output_audio = {
			"enabled": False,
			"engine": "google",
			"language": "en-US"
		}
		new["output"]["audio"] = output_audio
		print "\tINFO: added the following new notification channels: sms, audio. Enable them if interested"
		# remove options from email
		del new["output"]["email"]["module_digest"]
		new["output"]["email"]["enabled"] = new["output"]["email"]["realtime_alerts"]
		del new["output"]["email"]["realtime_alerts"]
		print "\tWARNING: 'module_digest' in 'email' has been deprecated, if 'daily_digest' is set to 'true' in the module, the digest will be sent"
		# add input
		new["input"] = {}
		new["input"]["settings"] = {}
		new["input"]["settings"]["algorithm"] = "token_set_ratio"
		new["input"]["settings"]["score"] = 50
		# remove options from slack
		new["output"]["slack"]["enabled"] = new["output"]["slack"]["realtime_alerts"]
		del new["output"]["slack"]["realtime_alerts"]
		new["input"]["slack"] = {}
		new["input"]["slack"]["enabled"] = new["output"]["slack"]["interactive_bot"]
		del new["output"]["slack"]["interactive_bot"]
		# add skin
		new["gui"]["skin"] = "blue"
		# add pws
		pws =  {
			"enabled": False,
			"username": "",
			"password": "",
			"publishing_interval": 10,
			"data": {
				"tempf": "outdoor:temperature:external",
				"humidity": "outdoor:humidity:external",
				"baromin": "outdoor:pressure:external"
			}
		  }
		new["pws"] = pws
		# add audio input
		input_audio = {
			  "enabled": False,
			  "engine": "google",
			  "language": "en-US",
			  "echo_request": False,
			  "recorder": {
				"max_duration": 60,
				"start_duration": 0.1,
				"start_threshold": 1,
				"end_duration": 3,
				"end_threshold": 0.1
			   }
			}
		new["input"]["audio"] = input_audio
		print "\tINFO: added audio input. Enable it if interested"
		# cycle through the modules
		group_to_delete = []
		group_summary_exclude = {}
		for module in new["modules"]:
			module_id = module["module_id"]
			if "display_name" in module:
				display_name = {"en": module["display_name"]}
				module["display_name"] = display_name
			# add uptime rule
			if module_id == "system":
				uptime_rule = {
				  "rule_id": "system_reboot",
				  "display_name": "The system has been recently rebooted",
				  "enabled": True,
				  "severity": "info",
				  "run_every": "5 minutes",
				  "conditions": [
				    "last_uptime < prev_uptime"
				  ],
				  "definitions": {
					  "last_uptime": "system:runtime:uptime,-1,-1",
					  "prev_uptime": "system:runtime:uptime,-2,-2"
				  }
				}
				module["rules"].append(uptime_rule)
				uptime_sensor = {
				  "module_id": "system",
				  "group_id": "runtime",
				  "sensor_id": "uptime",
				  "enabled": True,
				  "display_name": "uptime",
				  "plugin": {
				    "plugin_name": "system",
				    "measure": "uptime",
				    "polling_interval": 10
				  },
				  "format": "int"
				}
				module["sensors"].append(uptime_sensor)
				print "\tINFO: a rule called 'system_reboot' to notify when the system reboots has been added for your convenience"
			if "widgets" in module:
				for i in range(len(module["widgets"])):
					for j in range(len(module["widgets"][i])):
						widget = module["widgets"][i][j]
						# update display_name
						if "display_name" in widget:
							display_name = {"en": widget["display_name"]}
							widget["display_name"] = display_name
						for k in range(len(widget["layout"])):
							layout = widget["layout"][k]
						       # update display_name
							if "display_name" in layout:
								display_name = {"en": layout["display_name"]}
								layout["display_name"] = display_name
							# add tracking to map
							if "type" in layout and layout["type"] == "map": 
								layout["tracking"] = True
								# delete the data from the map sensors since format has changed
								if "group" in layout: group_to_delete.append(layout["group"])
			if "rules" in module:
				for i in range(len(module["rules"])):
					rule = module["rules"][i]
					# update display_name
					if "display_name" in rule:
						display_name = {"en": rule["display_name"]}
						rule["display_name"] = display_name
					for a,b in rule["definitions"].iteritems():
						# rename timestam in elapsed in rule definition
						if not utils.is_number(b) and ",timestamp" in b: rule["definitions"][a] = b.replace(",timestamp",",elapsed")
			if "sensors" in module:
				for i in range(len(module["sensors"])):
					sensor = module["sensors"][i]
					# add enabled
					sensor["enabled"] = True
				        # update display_name
					if "display_name" in sensor:
						display_name = {"en": sensor["display_name"]}
						sensor["display_name"] = display_name
					# add module_id to each sensor
					sensor["module_id"] = module_id
					# remove group_summary_exclude
					if "group_summary_exclude" in sensor:
						group_summary_exclude[module_id+":"+sensor["group_id"]] = module_id+":"+sensor["group_id"]+":"+sensor["sensor_id"]
						del sensor["group_summary_exclude"]
					# convert single_instance
					if "single_instance" in sensor: 
						sensor["retention"] = {}
						sensor["retention"]["realtime_count"] = 1
						del sensor["single_instance"]
					if "plugin" in sensor:
						# rename csv plugin settings
						if sensor["plugin"]["plugin_name"] == "csv":
							if "date_position" in sensor:
								sensor["plugin"]["date_position"] = sensor["plugin"]["date_index"]
								del sensor["plugin"]["date_index"]
							if "node_id" in sensor:
								sensor["plugin"]["filter"] = sensor["plugin"]["node_id"]
								del sensor["plugin"]["node_id"]
							if "node_id_index" in sensor:
								sensor["plugin"]["filter_position"] = sensor["plugin"]["node_id_index"]
								del sensor["plugin"]["node_id_index"]
							if "measure" in sensor:
								sensor["plugin"]["prefix"] = sensor["plugin"]["measure"]
								del sensor["plugin"]["measure"]
							if "measure_index" in sensor:
								sensor["plugin"]["value_position"] = sensor["plugin"]["measure_index"]
								del sensor["plugin"]["measure_index"]
						if sensor["plugin"]["plugin_name"] == "icloud":
							# device name mandatory
							sensor["plugin"]["device_name"] = ""
							print "\tWARNING: the 'icloud' plugin requires now a single 'device_name' to be set, please review all your sensors using this plugin"
							if "devices" in sensor["plugin"]:
								sensor["plugin"]["device"] = sensor["plugin"]["devices"][0]
						if sensor["plugin"]["plugin_name"] == "linux":
							# migrate the linux plugin
							if sensor["plugin"]["measure"] == "custom":
								# migrate to the command plugin
								del sensor["plugin"]["measure"]
								sensor["plugin"]["plugin_name"] = "command"
							else:
								# migrate to the system plugin
								sensor["plugin"]["plugin_name"] = "system"
		# add the power module
		new["modules"].append(power)
		print "\tINFO: a new module called 'power' has been added for rebooting/shutting down the system"
		# add the news module
		new["modules"].append(news)
		print "\tINFO: a new module called 'news' has been added for presenting the latest headlines"
		# second round
		for module in new["modules"]:
			module_id = module["module_id"]
			if "widgets" in module:
				for i in range(len(module["widgets"])):
					for j in range(len(module["widgets"][i])):
						widget = module["widgets"][i][j]
						for k in range(len(widget["layout"])):
							layout = widget["layout"][k]
							if layout["type"] == "sensor_group_summary" and layout["group"] in group_summary_exclude:
								# add exclude
								layout["exclude"] = []
								layout["exclude"].append(group_summary_exclude[layout["group"]])
		# delete from the db the sensors in group_to_delete
		for group in group_to_delete:
			sensors = utils.get_group(group)
			for sensor in sensors:
				print sensor["module_id"]+":"+sensor["group_id"]+":"+sensor["sensor_id"]
				db.delete(sensor["module_id"]+":"+sensor["group_id"]+":"+sensor["sensor_id"])
		# save the updated configuration
		config.save(json.dumps(new, default=lambda o: o.__dict__))
	if upgrade_db:
		print "Upgrading database..."
		version_key = conf["constants"]["db_schema"]["version"]
		db.set_simple(version_key,"2.2")

# upgrade from 2.2 to 2.3
def upgrade_2_3(version):
	upgrade_config = True
	upgrade_db = True
        conf = config.get_config(validate=False)
	target_version = conf["constants"]["version"]
        log.info("[Migration to v"+target_version+"]\n")
        backup(version)
	if upgrade_config and utils.file_exists(conf["constants"]["config_file"]):
		log.info("Upgrading configuration file...")
	        new = json.loads(conf["config_json"], object_pairs_hook=OrderedDict)
		default_mysensors_gateway = None
		# add bluetooth plugin
		if "bluetooth" not in new["plugins"]:
			bluetooth = {
				"adapter": "hci0"
			}
			new["plugins"]["bluetooth"] = bluetooth
		# migrate the mysensors plugin from dev2 to dev3
		if "mysensors" in new["plugins"] and "enabled" in new["plugins"]["mysensors"]:
			gateway_serial = {}
			gateway_serial["gateway_type"] = "serial"
			gateway_serial["enabled"] = True if new["plugins"]["mysensors"]["gateway_type"] == "serial" else False
			gateway_serial["gateway_id"] = "serial_1"
			gateway_serial["port"] = new["plugins"]["mysensors"]["gateways"]["serial"]["port"]
			gateway_serial["baud"] = new["plugins"]["mysensors"]["gateways"]["serial"]["baud"]
			if gateway_serial["enabled"]: default_mysensors_gateway = "serial_1"
                        gateway_ethernet = {}
                        gateway_ethernet["gateway_type"] = "ethernet"
                        gateway_ethernet["enabled"] = True if new["plugins"]["mysensors"]["gateway_type"] == "ethernet" else False
                        gateway_ethernet["gateway_id"] = "ethernet_1"
                        gateway_ethernet["hostname"] = new["plugins"]["mysensors"]["gateways"]["ethernet"]["hostname"]
                        gateway_ethernet["port"] = new["plugins"]["mysensors"]["gateways"]["ethernet"]["port"]
			if gateway_ethernet["enabled"]: default_mysensors_gateway = "ethernet_1"
                        gateway_mqtt = {}
                        gateway_mqtt["gateway_type"] = "mqtt"
                        gateway_mqtt["enabled"] = True if new["plugins"]["mysensors"]["gateway_type"] == "mqtt" else False
                        gateway_mqtt["gateway_id"] = "mqtt_1"
                        gateway_mqtt["port"] = new["plugins"]["mysensors"]["gateways"]["mqtt"]["port"]
                        gateway_mqtt["hostname"] = new["plugins"]["mysensors"]["gateways"]["mqtt"]["hostname"]
                        gateway_mqtt["subscribe_topic_prefix"] = new["plugins"]["mysensors"]["gateways"]["mqtt"]["subscribe_topic_prefix"]
                        gateway_mqtt["publish_topic_prefix"] = new["plugins"]["mysensors"]["gateways"]["mqtt"]["publish_topic_prefix"]
			if gateway_mqtt["enabled"]: default_mysensors_gateway = "mqtt_1"
			new["plugins"]["mysensors"]["gateways"] = []
			new["plugins"]["mysensors"]["gateways"].extend([gateway_serial,gateway_ethernet,gateway_mqtt])
			del new["plugins"]["mysensors"]["gateway_type"]
			del new["plugins"]["mysensors"]["enabled"]
		if "mysensors" not in new["plugins"]:
			mysensors = {
		                "gateways": [
				        {
				                "gateway_type": "serial",
                        			"gateway_id": "serial_1",
		                        	"enabled": False,
			                        "port": "/dev/ttyAMA0",
			                        "baud": 57600
				        },
				        {
			                        "gateway_type": "ethernet",
		        	                "gateway_id": "ethernet_1",
	                		        "enabled": false,
			                        "hostname": "localhost",
			                        "port": 5003
				        },
				        {
			                        "gateway_type": "mqtt",
			                        "gateway_id": "mqtt_1",
			                        "enabled": false,
			                        "hostname": "localhost",
			                        "port": 1883,
			                        "subscribe_topic_prefix": "mysensors-out",
			                        "publish_topic_prefix": "mysensors-in"
				        }
				]
		        }
			new["plugins"]["mysensors"] = mysensors
		for module in new["modules"]:
	        	module_id = module["module_id"]
	                if "widgets" in module:
	                	for i in range(len(module["widgets"])):
	                        	for j in range(len(module["widgets"][i])):
	                                	widget = module["widgets"][i][j]
	                                        for k in range(len(widget["layout"])):
	                                        	layout = widget["layout"][k]
	                                                # add actions to button
	                                                if "type" in layout and layout["type"] == "button" and "send" in layout and "actions" not in layout:
	                                                	layout["actions"] = ["send,"+layout["send"]]
								del layout["send"]
                        if "sensors" in module:
                                for i in range(len(module["sensors"])):
                                        sensor = module["sensors"][i]
					if "plugin" in sensor:
						if sensor["plugin"]["plugin_name"] == "mysensors":
							if default_mysensors_gateway is not None: sensor["plugin"]["gateway_id"] = default_mysensors_gateway
		# save the updated configuration
	        config.save(json.dumps(new, default=lambda o: o.__dict__))
	if upgrade_db:
		# update the version
		log.info("Upgrading the database...")
		db.set_version(target_version)

# main 
if __name__ == '__main__':
	# ensure it is run as root
	if os.geteuid() != 0: exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
	init_logger()
	log.info("Welcome to myHouse")
	log.info("------------------")
	# retrieve the version from the database
	version = db.get_version()
	# if requested set the current version manually
	if len(sys.argv) == 3 and sys.argv[1] == "--current-version": version = sys.argv[2]
	if version is None:
		log.info("ERROR: a previous version of myHouse was not found on the configured database")
		exit()
	log.info("Detected version: "+version)
	if version == conf["constants"]["version"]: 
		log.info("Already running the latest version ("+str(version)+"). Exiting.")
		exit()
	if version == "1.0": upgrade_2_0()
	elif version == "2.0": upgrade_2_1()
	elif version == "2.1": upgrade_2_2()
	elif version == "2.2" or version.startswith("2.3-dev"): upgrade_2_3(version)
	else:
		log.error("Unable to upgrade, unknown version "+version)
		exit()
	log.info("\nUpgrade completed. Please review the config.json file ensuring the configuration is correct, then run 'sudo python config.py' to verify there are no errors before restarting the service")

