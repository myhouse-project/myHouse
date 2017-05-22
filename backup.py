#!/usr/bin/python
import sys
import os

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()

# run the backup
def run(backup_id,suffix):
	for entry in conf["general"]["backup"]:
		# search the requested job
		if entry["backup_id"] != backup_id: continue
		# ignore disabled jobs
		if not entry["enabled"]: return
		log.info("Running backup job "+entry["backup_id"])
		# build up the command to run
		command = entry["command"].replace("%filename%",entry["filename"])
		command = command.replace("%target%",os.path.basename(entry["filename"])+"."+suffix)
		log.debug("Running backup command: "+command)
		log.debug(utils.run_command(command))

# schedule backup process
def schedule_all():
	# for each backup job
	for entry in conf["general"]["backup"]:
		# schedule the execution of the daily and weekly job
		if not entry["enabled"]: return
		log.info("Scheduling backup job "+entry["backup_id"])
                schedule.add_job(run,'cron',hour="0",minute="30",second=utils.randint(1,59),args=[entry["backup_id"],"daily"])
		schedule.add_job(run,'cron',day_of_week='sun',hour="0",minute="30",second=utils.randint(1,59),args=[entry["backup_id"],"weekly"])

# main
if __name__ == '__main__':
        if len(sys.argv) == 1:
                print "Usage: "+__file__+" <backup_id> <daily|weekly>"
        else:
                run(sys.argv[1],sys.argv[2])

