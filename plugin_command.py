#!/usr/bin/python
import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# poll the sensor
def poll(sensor):
	command = sensor['plugin']['command_poll']
	# run the poll command
	command = "cd '"+conf["constants"]["base_dir"]+"'; "+command
	return utils.run_command(command,timeout=conf["plugins"]["linux"]["timeout"])

# parse the data
def parse(sensor,data):
	data = str(data).replace("'","''")
	# no command parse, return the raw data
	if 'command_parse' not in sensor['plugin'] or sensor['plugin']['command_parse'] == "": return data
	command = sensor['plugin']['command_parse']
	return utils.run_command("cd '"+conf["constants"]["base_dir"]+"'; echo '"+data+"' |"+command,timeout=conf["plugins"]["linux"]["timeout"])

# return the cache schema
def cache_schema(sensor):
	return sensor['plugin']['command_poll']

# run a command
def send(sensor,data):
        # run the command in the script directory
        command = "cd '"+conf["constants"]["base_dir"]+"'; "+data
	utils.run_command(command,timeout=conf["plugins"]["linux"]["timeout"])
