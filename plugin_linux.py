#!/usr/bin/python
import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# define common commands
commands = {
	'cpu_user': {
		'command_poll': 'top -bn1',
		'command_parse': 'grep "Cpu(s)"|awk \'{print $2}\'',
	},
        'cpu_system': {
                'command_poll': 'top -bn1',
                'command_parse': 'grep "Cpu(s)"|awk \'{print $4}\'',
        },
        'ram_used': {
                'command_poll': 'free -m',
                'command_parse': 'grep Mem:|awk \'{print $3}\'',
        },
        'swap_used': {
                'command_poll': 'free -m',
                'command_parse': 'grep Swap:|awk \'{print $3}\'',
        },
        'load_1': {
                'command_poll': 'uptime',
                'command_parse': 'awk \'{gsub(",","",$(NF-2)); print $(NF-2)}\'',
        },
        'load_5': {
                'command_poll': 'uptime',
                'command_parse': 'awk \'{gsub(",","",$(NF-1)); print $(NF-1)}\'',
        },
        'load_15': {
                'command_poll': 'uptime',
                'command_parse': 'awk \'{gsub(",","",$(NF-0)); print $(NF-0)}\'',
        },
        'network_services': {
                'command_poll': 'netstat -tunap 2>/dev/null',
                'command_parse': 'grep tcp|grep LISTEN|wc -l',
        },
        'network_connections': {
                'command_poll': 'netstat -tunap 2>/dev/null',
                'command_parse': 'grep tcp|grep -v LISTEN|wc -l',
        },
        'temperature': {
                'command_poll': 'cat /sys/class/thermal/thermal_zone0/temp',
                'command_parse': 'awk \'{printf "%.1f",$0/1000}\'',
        },
}

# poll the sensor
def poll(sensor):
	command = commands[sensor['plugin']['measure']]['command_poll'] if sensor['plugin']['measure'] in commands else sensor['plugin']['command_poll']
	# run the command in the script directory
	command = "cd '"+conf["constants"]["script_dir"]+"'; "+command
	return utils.run_command(command,timeout=conf["plugins"]["linux"]["timeout"])

# parse the data
def parse(sensor,data):
	data = str(data).replace("'","''")
	command = commands[sensor['plugin']['measure']]['command_parse'] if sensor['plugin']['measure'] in commands else sensor['plugin']['command_parse']
	measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
	parsed = ""
	if command != "": 
		# run the command to parse the data
		parsed = utils.run_command("echo '"+data+"' |"+command,timeout=conf["plugins"]["linux"]["timeout"])
	else: 
		# use the input data as parsed data
		parsed = data
	measure["value"] = utils.normalize(parsed,conf["constants"]["formats"][sensor["format"]]["formatter"])
        # append the measure and return it
        measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	command = commands[sensor['plugin']['measure']]['command_poll'] if sensor['plugin']['measure'] in commands else sensor['plugin']['command_poll']
	return command

# run a command
def send(sensor,data):
        # run the command in the script directory
        command = "cd '"+conf["constants"]["script_dir"]+"'; "+data
	utils.run_command(command,timeout=conf["plugins"]["linux"]["timeout"])
