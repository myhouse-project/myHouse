#!/usr/bin/python
import simplejson as json
import constants
import time
from shutil import copyfile
from collections import OrderedDict

config = None

# return all the configuration settings as an object
def get_config():
        load()
        # attach constants
        config['constants'] = constants.get_constants()
        # adapt the units if needed
        if config["units"]["imperial"]:
                constants["formats"]["length"]["suffix"] = "in"
                constants["formats"]["length"]["formatter"] = "float_2"
		constants["formats"]["speed"]["suffix"] = "m/h"
        if config["units"]["fahrenheit"]:
                constants["formats"]["temperature"]["suffix"] = u'\u00B0F'
                constants["formats"]["temperature"]["formatter"] = "int"
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
        const = constants.get_constants()
        # open the config file
        with open(const['config_file'], 'r') as file:
                config_file = file.read()
	file.close()
	config = json.loads(config_file, object_pairs_hook=OrderedDict)

# save the configuration
def save(config_string):
	const = constants.get_constants()
        try:
		new_config = json.loads(config_string, object_pairs_hook=OrderedDict)
        except ValueError, e:
                log.warning("unable to save configuration, invalid JSON provided: "+config_string)
                return json.dumps("KO")
	copyfile(const['config_file'],const['config_file_backup'])
        with open(const['config_file'],'w') as file:
                file.write(json.dumps(new_config,indent=2))
        file.close()
	return json.dumps("OK")
