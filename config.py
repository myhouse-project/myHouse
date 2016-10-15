#!/usr/bin/python
import json
import constants
import yaml
import time
from collections import OrderedDict

config = None

# return all the configuration settings as an object
def get_config():
        load()
        # attach constants
        config['constants'] = constants.get_constants()
        # adapt the units if needed
        if config["general"]["imperial_units"]:
                constants["formats"]["length"]["suffix"] = "in"
                constants["formats"]["length"]["formatter"] = "float_2"
		constants["formats"]["speed"]["suffix"] = "m/h"
        if config["general"]["fahrenheit_temperature"]:
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
	config = ordered_load(config_file, yaml.SafeLoader)

# dump the configuration
def dump():
	print ordered_dump(config, Dumper=yaml.SafeDumper,indent=1,default_flow_style=False)

# load a yaml file into a OrderedDict
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
	class OrderedLoader(Loader):
        	pass
	def construct_mapping(loader, node):
        	loader.flatten_mapping(node)
	        return object_pairs_hook(loader.construct_pairs(node))
	OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,construct_mapping)
	return yaml.load(stream, OrderedLoader)

# dump a OrderedDict into a yaml file
def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
	class OrderedDumper(Dumper):
        	pass
	def _dict_representer(dumper, data):
        	return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,data.items())
	OrderedDumper.add_representer(OrderedDict, _dict_representer)
	return yaml.dump(data,stream, OrderedDumper, **kwds)

