#!/usr/bin/python
import sys
import getopt
import Adafruit_DHT

# defaults
device = "dht11"
pin = None

# settings
debug = False

# print usage
def usage():
	print "Usage: "+__file__+" -d <dht11|dht22> -p <pin>"
        sys.exit(1)

# run 
def run(device=device,pin=pin):
	# ensure the pin is provided
	if pin is None: exit("Pin is missing")
	# check the device
	if device == "dht11":
		sensor = Adafruit_DHT.DHT11
	elif device == "dht22":
		sensor = Adafruit_DHT.DHT22
	else: exit("Invalid device "+device)
	# read the measures
	humidity, temperature = Adafruit_DHT.read_retry(sensor,pin)
	if humidity is not None and temperature is not None and humidity <= 100:
		print('{0:0.1f}|{1:0.1f}'.format(temperature, humidity))

# main
if __name__ == '__main__':
	# read command line options
	try:
		opts, args = getopt.getopt(sys.argv[1:],"ht:p:")
	except getopt.GetoptError:
		usage()
	# parse command line options
	for opt, arg in opts:
		if opt == '-h': 
			usage()
		elif opt == '-d': 
			device = arg
		elif opt == '-p':
                        pin = arg
	run(device,pin)
