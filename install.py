#!/usr/bin/python
import sys
import os
import subprocess
import re
import logging
import logging.handlers

# variables
base_dir = os.path.abspath(os.path.dirname(__file__))
log_file = base_dir+"/logs/install.log"
service_template = base_dir+"/template_service.sh"
service_location = '/etc/init.d/myhouse'
filename = service_location.split('/')[-1]
dependencies = ["python-dev","redis-server","python-flask","python-redis","python-numpy","python-rpi.gpio","mosquitto","libttspico-utils","python-opencv","mpg123","sox","flac","pocketsphinx","python-feedparser","python-serial","screen"]
dependencies_python = ["APScheduler","slackclient","simplejson","python-Levenshtein","fuzzywuzzy","pyicloud","motionless","flask-compress","jsonschema","paho-mqtt","gTTS","SpeechRecognition","Adafruit-Python-DHT","Adafruit-ADS1x15","OPi.GPIO"]
inventory = []
inventory_python = []
log = logging.getLogger("install")

# determine if running on a raspberry
# return true if running on raspberry pi
def is_raspberry():
        with open("/proc/cpuinfo",'r') as file:
                cpu = file.read()
        file.close()
        if "BCM" in cpu: return True
        return False

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

# create an inventory of the software installed
def create_inventory(apt_update):
	if apt_update:
		# updating apt cache
		log.info("Refreshing apt cache (it may take a while)...")
		run_command("apt-get update")
	# create an inventory of the deb packages installed
	log.info("Creating an inventory of the installed packages...")
	output = run_command("dpkg -l")
	for line in output.split("\n"):
		package = re.findall("ii\s+(\S+)\s+",line)
		if package is None: continue
		if len(package) == 1: inventory.append(package[0].lower())
	log.info("\t- Listed "+str(len(inventory))+" packages")
	# create an inventory of all python modules installed
	log.info("Creating an inventory of the installed python modules...")
	output = run_command("pip list")
        for line in output.split("\n"):
                package = re.findall("^(\S+) \(",line)
		if package is None: continue
                if len(package) == 1: inventory_python.append(package[0].lower())
	log.info("\t- Listed "+str(len(inventory_python))+" packages")

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
		if ret != 0: log.debug("WARNING: during the execution of "+command+": "+output)
		return output

# install with apt an array of packages if not already installed
def install_packages(packages):
	for package in packages:
		if package == "python-rpi.gpio" and not is_raspberry(): continue
		if package.lower() in inventory:
			log.debug("\t- Skipping "+package+": already installed")
		else:
			log.info("\t- Installing package "+package+"...")
			log.debug(run_command("apt-get install -y "+package))

# install with pip an array of python modules if not already installed
def install_python(packages):
        for package in packages:
		if package == "OPi.GPIO" and is_raspberry(): continue
                if package.lower() in inventory_python:
			log.debug("\t - Skipping "+package+": already installed")
                else:
                        log.info("\t- Installing python module "+package+"...")
			log.debug(run_command("pip install "+package))

# check if pip is installed, otherwise install it
def install_pip():
	log.info("Verifying Python Packet Index...")
	ret = run_command("which pip",return_code=True)
	if ret == 0: return
	install_packages(["python-pip"])

# check if a file exists on the filesystem
def file_exists(file):
        return os.path.isfile(file)

# install the service if not already there
def install_service():
	if file_exists(service_location):
		log.debug("- Service already installed")
		return
        log.info("Installing the service...")
        # prepare the service template
        with open(service_template, 'r') as file:
                template = file.read()
        template = template.replace("#base_dir#",base_dir)
        # write the service script
        log.info("\t- Creating the service script...")
        with open(service_location,'w') as file:
                file.write(template)
        file.close()
        # make it executable
        run_command("chmod 755 "+service_location)
        # add it as a service
        log.info("\t- Adding it as a service...")
        run_command("update-rc.d "+filename+" defaults")
        # start the service
        log.info("\t- Starting the service...")
        run_command("service "+filename+" start")

def uninstall_service():
        log.info("- Uninstalling...")
        # stop the service
        log.info("\t- Stopping the service...")
        run_command("service "+filename+" stop")
        # remove the script
        log.info("\t- Uninstalling the service...")
        run_command("rm -f "+service_location)
        # disable the service
        run_command("update-rc.d -f "+filename+" remove")

# allow running it both as a module and when called directly
if __name__ == '__main__':
	# ensure it is run as root
	if os.geteuid() != 0:
        	exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
	init_logger()
	log.info("Welcome to myHouse")
	log.info("------------------")
	if len(sys.argv) == 2 and sys.argv[1] == "-u": 
		uninstall_service()
	else: 
		apt_update = True
		if len(sys.argv) == 2 and sys.argv[1] == "-q": apt_update = False
		create_inventory(apt_update)
		install_pip()
		log.info("Installing missing dependencies...")
		install_packages(dependencies)
		install_python(dependencies_python)
		install_service()
		log.info("Done! ")
		log.info("------------------")
		log.info("Access the web interface on http://raspberry.ip. If unavailable, review for errors the files install.log and myHouse.log into the 'logs' directory")

