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
	'application_database': {
		'command_poll': 'ls -alh /var/lib/redis/',
		'command_parse': 'grep dump.rdb|awk \'{print $5}\' |grep -o \'[0-9.]\\+\''
	},
	'uptime': {
		'command_poll': 'date -d \"$(uptime -s)\" +%s',
		'command_parse': ''
	},
	'logwatch': {
                'command_poll': 'logwatch --range yesterday --output stdout --format text',
                'command_parse': 'cat'
	},
	'reboot': {
                'command_poll': 'reboot',
                'command_parse': ''
	},
        'shutdown': {
                'command_poll': 'shutdown',
                'command_parse': ''
        },
	'application_logs': {
                'command_poll': 'tail -500 logs/myHouse.log',
                'command_parse': 'perl -ne \'/^\\[([^\\]]+)\\] \\[([^\\]]+)\\] (\\w+): (.+)$/;print \"$1|_|$2|_|$3|_|$4\\n\"\''
	},
	'system_logs': {
                'command_poll': 'tail -500 /var/log/messages',
                'command_parse': 'perl -ne \'/^(\\S+ \\S+ \\S+) \\S+ (\\S+): (.+)$/;print \"$1|_|$2|_|$3\\n\"\''
	}
}

# poll the sensor
def poll(sensor):
	if sensor['plugin']['measure'] not in commands:
		log.error("Invalid measure "+sensor['plugin']['measure'])
		return ""
	# run the poll command
	command_poll = commands[sensor['plugin']['measure']]["command_poll"]
	command = "cd '"+conf["constants"]["base_dir"]+"'; "+command_poll
	return utils.run_command(command,timeout=conf["plugins"]["system"]["timeout"])

# parse the data
def parse(sensor,data):
        if sensor['plugin']['measure'] not in commands:
                log.error("Invalid measure "+sensor['plugin']['measure'])
                return ""
	data = str(data).replace("'","''")
        command_parse = commands[sensor['plugin']['measure']]["command_parse"]
	# no command to run, return the raw data
	if command_parse == "": return data
	# run command parse
	command = "cd '"+conf["constants"]["base_dir"]+"'; echo '"+data+"' |"+command_parse
	return utils.run_command(command,timeout=conf["plugins"]["system"]["timeout"])

# return the cache schema
def cache_schema(sensor):
	return commands[sensor['plugin']['measure']]['command_poll']	
