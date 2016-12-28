#!/usr/bin/python
import sys
import getopt
import os.path

# defaults
device = None

# settings
debug = False

# print usage
def usage():
	print "Usage: "+__file__+" -d <device_address>"
        sys.exit(1)

# run 
def run(device):
	# ensure the device exists
	if device is None: exit("Device is missing")
	filename = "/sys/bus/w1/devices/"+device+"/w1_slave"
	if not os.path.isfile(filename): exit("File "+filename+" is missing")
	# read the file
	if debug: print "Reading temperature from "+filename
	file = open(filename, 'r')
	lines = file.readlines()
	file.close()
	# parse the file
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp = float(temp_string) / 1000.0
	print temp

# main
if __name__ == '__main__':
	# read command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hd:")
	except getopt.GetoptError:
		usage()
	# parse command line options
	for opt, arg in opts:
		if opt == '-h': 
			usage()
		elif opt == '-d': 
			device = arg
	run(device)
