#!/usr/bin/python
import Adafruit_ADS1x15

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# define the maxium voltage for each gain
gain_ratio = {
        "2/3": 6.144,
        "1": 4.096,
        "2": 2.048,
        "4": 1.024,
        "8": 0.512,
        "16": 0.256,
}

# poll the sensor
def poll(sensor):
	log.debug("Reading channel "+str(sensor["plugin"]["channel"])+" from "+sensor["plugin"]["type"]+"("+str(sensor["plugin"]["address"])+") with gain "+sensor["plugin"]["gain"]+" ("+str(gain_ratio[sensor["plugin"]["gain"]])+"V) output "+sensor["plugin"]["output"])
        # convert the address in hex
	address = int(sensor["plugin"]["address"][2:],16)
	# select the device
        if sensor["plugin"]["device"] == "ads1115": adc = Adafruit_ADS1x15.ADS1115(address=sensor["plugin"]["address"])
        elif sensor["plugin"]["device"] == "ads1015": adc = Adafruit_ADS1x15.ADS1015(address=sensor["plugin"]["address"])
	# read the value and return the raw value
        value = adc.read_adc(channel, gain=int(sensor["plugin"]["gain"]))
	log.debug("Read "+str(value))
	return value

# parse the data
def parse(sensor,data):
	max = 1
	# ads1115 is 16bit, ads1015 12 bit
        if sensor["plugin"]["device"] == "ads1115": max = 32768
        elif sensor["plugin"]["device"] == "ads1015": max = 2048
        # normalize the value
	value = float(data)
	# calculate the voltage based on the maximum voltage from the gain set
        volt = value*gain_ratio[sensor["plugin"]["gain"]]/max
	# return an arduino like value between 0 and 1024
        integer = int(volt*1024/gain_ratio[sensor["plugin"]["gain"]])
	# return a percentage based on the maximum value it can assume from the gain set
        percentage = int(volt*100/gain_ratio[sensor["plugin"]["gain"]])
        log.debug("Parsed "+str(value)+" -> "+str(volt)+"V -> "+str(integer)+"/1024 -> "+str(percentage)+"%")
        # return the output
        if sensor["plugin"]["output"] == "volt": return volt
        elif sensor["plugin"]["output"] == "raw": return value
        elif sensor["plugin"]["output"] == "integer": return integer
        elif sensor["plugin"]["output"] == "percentage": return percentage

# return the cache schema
def cache_schema(sensor):
	return sensor["plugin"]["address"]+"_"+str(sensor["plugin"]["channel"])
