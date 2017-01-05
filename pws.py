#!/usr/bin/python

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()
import sensors
import db

# variables
new_measures_only = False

# schedule the service
def schedule_all():
	log.info("starting pws module...")
	# schedule the run job
	schedule.add_job(run,'cron',minute="*/"+str(conf["pws"]["publishing_interval"]),second=utils.randint(1,59),args=[])

# publish an update
def run():
	url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
	measures = {}
	# prepare the custom parameters
	count = 0
	for field,sensor_key in conf["pws"]["data"].iteritems():
		# for each mapping, retrieve the sensor
		split = sensor_key.split(":")
		sensor = utils.get_sensor(split[0],split[1],split[2])
	        if sensor is None:
			log.warning("invalid sensor "+sensor_key+" associated to field "+field)
			continue
		# retrieve the data
		key = conf["constants"]["db_schema"]["root"]+":"+sensor_key
		data = db.range(key,withscores=True)
		if len(data) == 0: continue
		timestamp = data[0][0]
		value = data[0][1]
		# do not send measure already sent
		if new_measures_only and timestamp < utils.now()-conf["pws"]["publishing_interval"]*60: 
			continue
		# perform the appropriate conversion
		if field in ["windspeedmph","windgustmph","windspdmph_avg2m","windgustmph_10m"] and not conf["general"]["units"]["imperial"]:
			value = utils.speed_unit(value,force=True)
		if field in ["dewptf","tempf","soiltempf"] and not conf["general"]["units"]["fahrenheit"]:
			value = utils.temperature_unit(value,force=True)
		if field in ["rainin","dailyrainin","baromin"] and not conf["general"]["units"]["imperial"]:
			value = utils.pressure_unit(value,force=True)
		measures[field] = value
		count = count + 1
	# if at least one parameter needs to be updated
	if count > 0:
		log.debug("Prepare uploading to pws "+str(measures))
		# prepare the common parameter
		params = {}
	 	params["action"] = "updateraw"
	        params["ID"] = conf["pws"]["username"]
        	params["PASSWORD"] = conf["pws"]["password"]
	        params["dateutc"] = "now"
		params.update(measures)
		response = utils.web_get(url,params=params)
		if "success" in response: log.info("Updated the PWS "+conf["pws"]["username"]+" with: "+str(measures))
		else: log.error("failed to update the PWS: "+str(response))
		
# main
if __name__ == '__main__':
	run()

