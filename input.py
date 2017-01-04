#!/usr/bin/python
import sys
import time
import datetime

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import scheduler
schedule = scheduler.get_scheduler()
import slack
import smtp
import audio

# run all the input services
def run():
	# schedule module summary report
        for module in conf["modules"]:
		if not module["enabled"]: continue
		if "daily_digest" not in module: continue
                if module["daily_digest"]:
                        schedule.add_job(smtp.module_digest,'cron',hour="23",minute="55",second=utils.randint(1,59),args=[module["module_id"]])
                        log.info("["+module['module_id']+"] scheduling daily module digest")
	# schedule alert summary report
	if conf["output"]["email"]["alerts_digest"]: 
		log.info("scheduling daily alert digest")
		schedule.add_job(smtp.alerts_digest,'cron',hour="0",minute="55",args=[])
	# run slack bot
	if conf["input"]["slack"]["enabled"]: schedule.add_job(slack.run,'date',run_date=datetime.datetime.now())
	# listen for voice commands
	if conf["input"]["audio"]["enabled"]: schedule.add_job(audio.listen,'date',run_date=datetime.datetime.now())

# main
if __name__ == '__main__':
	schedule.start()
        run()
       	while True:
               	time.sleep(1)
