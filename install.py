#!/usr/bin/python
import sys
import os

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
filename = conf['constants']['service_location'].split('/')[-1]

# install all the dependencies
def install_deps():
	log.info("Preparing dependencies...")
	log.info("Installing redis...")
	log.debug(utils.run_command("apt-get install redis"))
	log.info("Installing flask...")
	log.debug(utils.run_command("apt-get install python-flask"))
        log.info("Installing python-redis...")
        log.debug(utils.run_command("apt-get install python-redis"))
        log.info("Installing python-numphy...")
        log.debug(utils.run_command("apt-get install python-numpy"))
        log.info("Installing python-rpi.gpio...")
        log.debug(utils.run_command("apt-get install python-rpi.gpio"))
        log.info("Installing python-apscheduler...")
        log.debug(utils.run_command("pip install APScheduler"))
        log.info("Installing python-slackclient...")
        log.debug(utils.run_command("pip install slackclient"))
        log.info("Installing python-simplejson...")
        log.debug(utils.run_command("pip install simplejson"))
        log.info("Installing python-levenshtein...")
        log.debug(utils.run_command("pip install python-Levenshtein"))
        log.info("Installing python-fuzzywuzzy...")
        log.debug(utils.run_command("pip install fuzzywuzzy"))
        log.info("Installing python-pyicloud...")
        log.debug(utils.run_command("pip install pyicloud"))
        log.info("Installing python-motionless...")
        log.debug(utils.run_command("pip install motionless"))
        log.info("Installing python-flask-compress...")
        log.debug(utils.run_command("pip install flask-compress"))
        log.info("Installing python-jsonschema...")
        log.debug(utils.run_command("pip install jsonschema"))

# installation routine
def install():
	install_deps()
	log.info("Installing the program...")
	# prepare the service template
	with open(conf['constants']['service_template'], 'r') as file:
		template = file.read()
	template = template.replace("#base_dir#",conf['constants']['base_dir'])
	# write the service script
	log.info("Creating the service script...")
	with open(conf['constants']['service_location'],'w') as file:
		file.write(template)
	file.close()
	# make it executable
	utils.run_command("chmod 755 "+conf['constants']['service_location'])
	# add it as a service
	log.info("Adding it as a service...")
	log.debug(utils.run_command("update-rc.d "+filename+" defaults"))
	# start the service
	log.info("Starting the service...")
	log.debug(utils.run_command("service "+filename+" start"))
	log.info("Done")

# uninstall routine
def uninstall():
	log.info("Uninstalling the program...")
        # stop the service
	log.info("Stopping the service...")
        log.debug(utils.run_command("service "+filename+" stop"))
	# remove the script
	log.info("Uninstalling the service...")
	log.debug(utils.run_command("rm -f "+conf['constants']['service_location']))
	# disable the service
	log.debug(utils.run_command("update-rc.d -f "+filename+" remove"))

# ensure it is run as root
if os.geteuid() != 0:
        exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
# run the installation
log.info("Welcome to myHouse v"+conf["constants"]["version_string"])
if len(sys.argv) == 2 and sys.argv[1] == "-u": uninstall()
else: install()


