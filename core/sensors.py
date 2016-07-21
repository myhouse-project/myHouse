#!/usr/bin/python
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../")
import core
import core.db

logger = core.get_logger(__name__)
config = core.get_config()

sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../sensors")
import ds18b20
import wunderground

def read(module,sensor,measure):
	# read the data
        data = module.read(sensor,measure)
        # store it in the cache
        core.db.set(core.db.schema["sensors_cache"]+":"+sensor["id"]+":"+module.cache(measure),data,core.now())

def parse(module,sensor,measure):
	# parse the data out of the cache
        data = core.db.range(core.db.schema["sensors_cache"]+":"+sensor["id"]+":"+module.cache(measure),withscores=False)[0]
	print "->"+data
        return module.parse(sensor,measure,data)


def main(req_id,req_measure,task):
	for sensor in config["sensors"]:
		if sensor["id"] == req_id or req_id == "-": 
	                # determine the module to use
	                if sensor["plugin"] == "ds18b20": module = ds18b20
        	        elif sensor["plugin"] == "wunderground": module = wunderground
			else: logger.error("Plugin "+sensor["plugin"]+" not supported")

			for measure in sensor["measures"]:
				if measure == req_measure or req_measure == "-":
					logger.info(sensor["id"]+" "+measure+" "+task)
					# execute the task
					if task == "read": 
						read(module,sensor,measure)
					if task == "parse":
						logger.info("Parsed: "+str(core.normalize(parse(module,sensor,measure))))
					if task == "save":
						timestamp = 0
						# get the data out of the cache
						if core.db.exists(core.db.schema["sensors_cache"]+":"+sensor["id"]+":"+module.cache(measure)):
							data = core.db.range(core.db.schema["sensors_cache"]+":"+sensor["id"]+":"+measure,withscores=True)
							timestamp = data[0][0]
						# if too old, refresh it
						if core.now() - timestamp > core.sensors_expire:
							read(module,sensor,measure)
						value = core.normalize(parse(module,sensor,measure))
						logger.info("Read "+str(sensor["id"])+" "+measure+" ("+sensor["plugin"]+"): "+str(value))
						core.db.set(core.db.schema["sensors"]+":"+sensor["id"]+":"+measure,value,core.now())
		

# allow running it both as a module and when called directly
if __name__ == '__main__':
        main(sys.argv[1],sys.argv[2],sys.argv[3])

