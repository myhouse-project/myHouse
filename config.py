#!/usr/bin/python
import simplejson as json
import constants
import time
import sys
import copy
from shutil import copyfile
from collections import OrderedDict
import jsonschema

config = None

# return all the configuration settings as an object
def get_config():
	# load the configuration from the file
        load()
        return config

# return all the configuration settings as a json object
def get_json_config():
        return json.dumps(get_config(), default=lambda o: o.__dict__)

# reload the configuration
def reload(): 
	config = None
	load()

# load the configuration from file
def load():
	# if the config is already loaded return
	global config
        if config is not None: return
	# load the constants
        const = constants.get_constants()
        # open the config file and load it
        with open(const['config_file'], 'r') as file:
                config_file = file.read()
	file.close()
	config = json.loads(config_file, object_pairs_hook=OrderedDict)
        # store the raw configuration into a variable
        config["config_json"] = config_file
	# load config schema
        with open(const['config_file_schema'], 'r') as file:
                const['config_schema_json'] = file.read()
        file.close()
        # adapt the units if needed
        if config["units"]["imperial"]:
                const["formats"]["length"]["suffix"] = "in"
                const["formats"]["length"]["formatter"] = "float_2"
                const["formats"]["speed"]["suffix"] = "m/h"
        if config["units"]["fahrenheit"]:
                const["formats"]["temperature"]["suffix"] = u'\u00B0F'
                const["formats"]["temperature"]["formatter"] = "int"
        # attach the constants
        config['constants'] = const
	# validate the configuration against the schema
	try:
		jsonschema.validate(json.loads(config["config_json"]),json.loads(const['config_schema_json']))
	except Exception,e:
		print "Error loading the confiugration file: "+str(e)
		sys.exit(1)

# save the configuration
def save(config_string):
	const = constants.get_constants()
        try:
		new_config = json.loads(config_string, object_pairs_hook=OrderedDict)
        except ValueError, e:
                print "unable to save configuration, invalid JSON provided: "+config_string
                return json.dumps("KO")
	copyfile(const['config_file'],const['config_file_backup'])
        with open(const['config_file'],'w') as file:
                file.write(json.dumps(new_config,indent=2))
        file.close()
	return json.dumps("OK")

# main
if __name__ == '__main__':
	get_config()
