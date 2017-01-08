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
import sensors

db_file = "/var/lib/redis/dump.rdb"
debug = False

# change into a given database number
def change_db(database):
        db.db = None
        conf['db']['database'] = database

# run a command and return the output
def run_command(command):
        if debug: print "Executing "+command
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        for line in process.stdout.readlines():
                output = output+line
        if debug: print output.rstrip()

# backup the database and the configuration file
def backup(version):
	if not utils.file_exists(db_file): exit("unable to find the database at "+db_file)
	backup_db_file = conf["constants"]["tmp_dir"]+"/dump.rdb_"+str(version)
	print "Backing up the database "+db_file+" into "+backup_db_file
	utils.run_command("cp "+db_file+" "+backup_db_file)
        backup_config_file = conf["constants"]["tmp_dir"]+"/config.json_"+str(version)
        print "Backing up the configuration file "+conf["constants"]["config_file"]+" into "+backup_config_file
        utils.run_command("cp "+conf["constants"]["config_file"]+" "+backup_config_file)

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
	upgrade_conf = False
	upgrade_service = True
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
        upgrade_db = False
        upgrade_conf = True
	upgrade_modules = False
	# END
        conf = config.get_config(validate=False)
        print "[Migration from v2.1 to v2.2]\n"
#        backup("2.1")
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
		# add the mqtt plugin
		new["plugins"]["mqtt"] = {}
		new["plugins"]["mqtt"]["enabled"] = False
		new["plugins"]["mqtt"]["hostname"] = "localhost"
		new["plugins"]["mqtt"]["port"] = 1883
		# add the ds18b20 plugin
		new["plugins"]["ds18b20"] = None
		# add the dht plugin
		new["plugins"]["dht"] = None
		# add the ads1x15 plugin
		new["plugins"]["ads1x15"] = None
		print "\tINFO: please be aware the following new plugins are now available: earthquake, mqtt, ds18b20, dht, ads1x15"
		# add general
		new["general"] = {}
		new["general"]["latitude"] = 0
		new["general"]["longitude"] = 0
		print "\tWARNING: different plugins use the new 'latitude' and 'longitude' in 'general', customize them"
		# move units and timeframe under general
		new["general"]["units"] = conf["units"]
		del new["units"]
                new["general"]["timeframes"] = conf["timeframes"]
                del new["timeframes"]
		# migrate sections
		new_sections = {}
		for section in new["gui"]["sections"]: new_sections[section] = section
		new["gui"]["sections"] = new_sections
		# add the power module
		power =  {
		      "module_id": "power",
		      "section_id": "System",
		      "display_name": "Reboot/Shutdown",
		      "icon": "fa-power-off",
		      "enabled": True,
		      "widgets": [
        		[
		          {
		            "widget_id": "reboot",
		            "display_name": "Reboot the system",
		            "enabled": True,
		            "size": 4,
		            "offset": 1,
		            "layout": [
		              {
		                "type": "button",
		                "display_name": "Reboot",
			        "send": "power/command/reboot/run/poll"
		              }
		            ]
	                   },
                           {
		            "widget_id": "shutdown",
		            "display_name": "Shutdown the system",
		            "enabled": True,
		            "size": 4,
	                    "offset": 2,
		            "layout": [
		              {
		                "type": "button",
                                "display_name": "Shutdown",
                		"send": "power/command/shutdown/run/poll"
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
		new["modules"].append(power)
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
		print "\tWARNING: 'location' in 'plugins/wunderground' and 'plugins/weatherchannel' has been precated, use e 'latitude' and 'longitude' in 'general' instead"
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
		print "\tINFO: added audio input. Enabled it if interested"
		# cycle through the modules
		group_to_delete = []
		group_summary_exclude = {}
                for module in new["modules"]:
			module_id = module["module_id"]
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
			          "display_name": "uptime",
			          "plugin": {
			            "plugin_name": "system",
			            "measure": "uptime",
			            "polling_interval": 10
			          },
			          "format": "int"
			        }
				module["sensors"].append(uptime_sensor)
				print "\tINFO: I've added a rule called 'system_reboot' to notify when the system reboots"
                        if "widgets" in module:
                                for i in range(len(module["widgets"])):
                                        for j in range(len(module["widgets"][i])):
                                                widget = module["widgets"][i][j]
                                                for k in range(len(widget["layout"])):
                                                        layout = widget["layout"][k]
							# add tracking to map
							if "type" in layout and layout["type"] == "map": 
								layout["tracking"] = True
								# delete the data from the map sensors since format has changed
								group_to_delete.append(layout["group"])
			if "rules" in module:
				for i in range(len(module["rules"])):
					rule = module["rules"][i]
					for a,b in rule["definitions"].iteritems():
						# rename timestam in elapsed in rule definition
						if not utils.is_number(b) and ",timestamp" in b: rule["definitions"][a] = b.replace(",timestamp",",elapsed")
                        if "sensors" in module:
                                for i in range(len(module["sensors"])):
                                        sensor = module["sensors"][i]
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
							print "\tWARNING: the 'icloud' plugin requires a single 'device_name' to be set, please review all your sensors using this plugin"
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

	if upgrade_modules:
		print "Installing additional dependencies..."
	        print "\tInstalling python-paho-mqtt..."
	        run_command("pip install paho-mqtt")
	        print "\tInstalling mosquitto..."
	        run_command("apt-get install -y mosquitto")
	        print "\tInstalling picotts..."
	        run_command("apt-get install -y libttspico-utils")
	        print "\tInstalling python-opencv..."
	        run_command("apt-get install -y python-opencv")
	        print "\tInstalling python-gtts..."
	        run_command("pip install gTTS")
	        print "\tInstalling mpg123..."
	        run_command("apt-get install -y mpg123")
	        print "\tInstalling python-speech-recognition..."
	        run_command("pip install SpeechRecognition")
	        print "\tInstalling sox..."
	        run_command("apt-get install -y sox")
	        print "\tInstalling flac..."
	        run_command("apt-get install -y flac")
	        print "\tInstalling pocketsphinx..."
	        run_command("apt-get install -y pocketsphinx")
        	print "\tInstalling python-dht..."
	        run_command("pip install Adafruit_Python_DHT")
	        print "\tInstalling python-ads1x15..."
	        run_command("pip install Adafruit_ADS1x15")
        if upgrade_db:
                print "Upgrading database..."
                version_key = conf["constants"]["db_schema"]["version"]
                db.set_simple(version_key,"2.2")

# main 
def main():
	# ensure it is run as root
	if os.geteuid() != 0:
	        exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
	print "Welcome to myHouse Upgrade Utility"
	print "-----------------------------------------"
	# retrieve the version from the database
	version_key = conf["constants"]["db_schema"]["version"]
	version = None
	if not db.exists(version_key): version = "1.0"
	else: version = db.get(version_key)
	print "Detected version: "+version
	if version == conf["constants"]["version"]: exit("Already running the latest version ("+str(version)+"). Exiting.")
	if version == "1.0": upgrade_2_0()
	if version == "2.0": upgrade_2_1()
	if version == "2.1": upgrade_2_2()

# run main()
main()
