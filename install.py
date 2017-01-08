#!/usr/bin/python
import sys
import os
import subprocess

# variables
base_dir = os.path.abspath(os.path.dirname(__file__))
service_template = base_dir+"/template_service.sh"
service_location = '/etc/init.d/myhouse'
filename = service_location.split('/')[-1]
debug = False

# run a command and return the output
def run_command(command):
	if debug: print "Executing "+command
	process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output = ''
	for line in process.stdout.readlines():
		output = output+line
	if debug: print output.rstrip()

# install all the dependencies
def install_deps():
	print "Preparing dependencies..."
	print "Installing redis..."
	run_command("apt-get install -y redis-server")
	print "Installing flask..."
	run_command("apt-get install -y python-flask")
	print "Installing python-redis..."
	run_command("apt-get install -y python-redis")
	print "Installing python-numphy..."
	run_command("apt-get install -y python-numpy")
	print "Installing python-rpi.gpio..."
	run_command("apt-get install -y python-rpi.gpio")
	print "Installing python-apscheduler..."
	run_command("pip install APScheduler")
	print "Installing python-slackclient..."
	run_command("pip install slackclient")
	print "Installing python-simplejson..."
	run_command("pip install simplejson")
	print "Installing python-levenshtein..."
	run_command("pip install python-Levenshtein")
	print "Installing python-fuzzywuzzy..."
	run_command("pip install fuzzywuzzy")
	print "Installing python-pyicloud..."
	run_command("pip install pyicloud")
	print "Installing python-motionless..."
	run_command("pip install motionless")
	print "Installing python-flask-compress..."
	run_command("pip install flask-compress")
	print "Installing python-jsonschema..."
	run_command("pip install jsonschema")
	# from v2.2
	print "Installing python-paho-mqtt..."
	run_command("pip install paho-mqtt")
	print "Installing mosquitto..."
	run_command("apt-get install -y mosquitto")
	print "Installing picotts..."
	run_command("apt-get install -y libttspico-utils")
	print "Installing python-opencv..."
	run_command("apt-get install -y python-opencv")
	print "Installing python-gtts..."
	run_command("pip install gTTS")
	print "Installing mpg123..."
	run_command("apt-get install -y mpg123")
	print "Installing python-speech-recognition..."
	run_command("pip install SpeechRecognition")
	print "Installing sox..."
	run_command("apt-get install -y sox")
	print "Installing flac..."
	run_command("apt-get install -y flac")
	print "Installing pocketsphinx..."
	run_command("apt-get install -y pocketsphinx")
	print "Installing python-dht..."
	run_command("pip install Adafruit_Python_DHT")
	print "Installing python-ads1x15..."
	run_command("pip install Adafruit_ADS1x15")

# installation routine
def install():
	install_deps()
	print "Installing the program..."
	# prepare the service template
	with open(service_template, 'r') as file:
		template = file.read()
	template = template.replace("#base_dir#",base_dir)
	# write the service script
	print "Creating the service script..."
	with open(service_location,'w') as file:
		file.write(template)
	file.close()
	# make it executable
	run_command("chmod 755 "+service_location)
	# add it as a service
	print "Adding it as a service..."
	run_command("update-rc.d "+filename+" defaults")
	# start the service
	print "Starting the service..."
	run_command("service "+filename+" start")
	print "Done"

# uninstall routine
def uninstall():
	print "Uninstalling the program..."
	# stop the service
	print "Stopping the service..."
	run_command("service "+filename+" stop")
	# remove the script
	print "Uninstalling the service..."
	run_command("rm -f "+service_location)
	# disable the service
	run_command("update-rc.d -f "+filename+" remove")

# ensure it is run as root
if os.geteuid() != 0:
	exit("ERROR: You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
# run the installation
print "Welcome to myHouse"
if len(sys.argv) == 2 and sys.argv[1] == "-u": uninstall()
else: install()


