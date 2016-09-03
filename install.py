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

# installation routine
def install():
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
	log.info(utils.run_command("update-rc.d "+filename+" defaults"))
	# start the service
	log.info("Starting the service...")
	log.info(utils.run_command("service "+filename+" start"))
	log.info("Done")

# uninstall routine
def uninstall():
	log.info("Uninstalling the program...")
        # stop the service
	log.info("Stopping the service...")
        log.info(utils.run_command("service "+filename+" stop"))
	# remove the script
	log.info("Uninstalling the service...")
	log.info(utils.run_command("rm -f "+conf['constants']['service_location']))
	# disable the service
	log.info(utils.run_command("update-rc.d -f "+filename+" remove"))

# ensure it is run as root
if os.geteuid() != 0:
        exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
# run the installation
log.info("Welcome to myHouse v"+conf["constants"]["version_string"])
if len(sys.argv) == 2 and sys.argv[1] == "-u": uninstall()
else: install()


