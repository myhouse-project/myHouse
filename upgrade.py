#!/usr/bin/python

import logging
import os
import sys
import json
from collections import OrderedDict

import config
conf = config.get_config(validate=False)
import utils
import db
import sensors

db_file = "/var/lib/redis/dump.rdb"

# change into a given database number
def change_db(database):
        db.db = None
        conf['db']['database'] = database

def backup(version):
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

# main 
def main():
	# ensure it is run as root
	if os.geteuid() != 0:
	        exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
	print "Welcome to myHouse v"+conf["constants"]["version_string"]+" Upgrade Utility"
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

main()
