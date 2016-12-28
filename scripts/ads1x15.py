#!/usr/bin/python

import Adafruit_ADS1x15
import sys
import getopt

# defaults
channel = 0
gain = 1
device = "ADS1115"
address = 0x48
output = "integer"

# settings
debug = False
gain_ratio = {
        "2/3": 6.144,
        "1": 4.096,
        "2": 2.048,
        "4": 1.024,
        "8": 0.512,
	"16": 0.256,
}

# print usage
def usage():
	print "Usage: "+__file__+" -c <channel> -g <gain> -d <ADS1115|ADS1015> -a <i2c_address> -o <volt|integer|percentage|raw>"
        sys.exit(1)

# run 
def run(channel=channel,gain=gain,device=device,address=address):
	if debug: print "Reading channel "+str(channel)+" from "+device+"("+str(address)+") with gain "+str(gain)+" ("+str(gain_ratio[str(gain)])+"V) output "+output
	# setup the device
	max = 1
	if device == "ADS1115": 
		adc = Adafruit_ADS1x15.ADS1115(address=address)
		max = 32768
	elif device == "ADS1015": 
		adc = Adafruit_ADS1x15.ADS1015(address=address)
		max = 2048
	else: exit("Invalid device "+device)
	# check the gain
	if str(gain) not in ["2/3","1","2","4","8","16"]: exit("Invalid gain "+gain)
	# read the value
	value = adc.read_adc(channel, gain=gain)
	# normalize the value
	volt = value*gain_ratio[str(gain)]/max
	integer = int(volt*1024/gain_ratio[str(gain)])
	percentage = int(volt*100/gain_ratio[str(gain)])
	if debug: print "Read "+str(value)+" -> "+str(volt)+"V -> "+str(integer)+"/1024 -> "+str(percentage)+"%"
	# print the output
	if output == "volt": print volt
	elif output == "raw": print value
	elif output == "integer": print integer
	elif output == "percentage": print percentage
	else: exit("Invalid output "+output) 

# main
if __name__ == '__main__':
	# read command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:],"ha:c:g:d:o:")
	except getopt.GetoptError:
		usage()
	# parse command line options
	for opt, arg in opts:
		if opt == '-h': 
			usage()
		elif opt == '-c': 
			channel = int(arg)
		elif opt == '-g': 
			gain = int(arg)
		elif opt == '-d': 
			device = arg
		elif opt == '-a': 
			address = int(arg[2:],16)
		elif opt == '-o':
			output = arg
	run(channel,gain,device,address)
