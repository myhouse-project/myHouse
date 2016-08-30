#!/usr/bin/python

import subprocess

import utils
import logger
log = logger.get_logger(__name__)

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


# run a command and return the output
def execute(command):
	log.debug("Executing "+command)
	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        for line in process.stdout.readlines():
        	output = output+line
	return output.rstrip()
	

# poll the sensor
def poll(sensor):
	command = commands[sensor['plugin']['request']]['command_poll'] if sensor['plugin']['request'] in commands else sensor['plugin']['command_poll']
	return execute(command)

# parse the data
def parse(sensor,data):
	command = commands[sensor['plugin']['request']]['command_parse'] if sensor['plugin']['request'] in commands else sensor['plugin']['command_parse']
	measures = []
        measure = {}
        measure["key"] = sensor["sensor_id"]
	parsed = execute("echo '"+str(data)+"' |"+command)
	measure["value"] = float(parsed)
        # append the measure and return it
        measures.append(measure)
        return measures

# return the cache schema
def cache_schema(sensor):
	command = commands[sensor['plugin']['request']]['command_poll'] if sensor['plugin']['request'] in commands else sensor['plugin']['command_poll']
	return command

