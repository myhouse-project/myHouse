#!/usr/bin/python
import sys
import datetime
import json

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import smtp
import alerter

# variables
run_generate_charts = True

# return the HTML template of the widget
def get_widget_template(title,body):
	template = '<tr class="total" style="font-family: \'Helvetica Neue\',Helvetica,Arial,sans-serif; \
	box-sizing: border-box; font-size: 14px; margin: 0;"><td class="alignright" width="80%" style="font-family: \'Helvetica \
	Neue\',Helvetica,Arial,sans-serif; box-sizing: border-box; font-size: 14px; vertical-align: top; text-align: center; border-top-width: 2px; \
	border-top-color: #333; border-top-style: solid; border-bottom-color: #333; border-bottom-width: 2px; border-bottom-style: solid; font-weight: 700; \
	margin: 0; padding: 5px 0;" valign="top">#title# \
	<br>#body# \
	</td></tr>'
	template = template.replace("#body#",body)
	template = template.replace("#title#",title)
	return template

# send out the email notification
def run():
	alerts = ['alert','warning','info']
	date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	title = "Alerts "+date
	# load and prepare the template
        with open(conf['constants']['email_template'], 'r') as file:
                template = file.read()
        template = template.replace("#date#",date)
        template = template.replace("#url#",conf['web']['url'])
	template = template.replace("#version#",conf['constants']['version_string'])
	template = template.replace("#title#",title)
        for severity in alerts:
		# for each severity
		text = ""
		data = json.loads(alerter.web_get_data(severity))
		if len(data) == 0: continue
		# merge the alerts together
		for alert in data: 
			text = "<small>* "+alert+" *</small><br>"+text 
		template = template.replace("<!-- widgets -->",get_widget_template(severity.capitalize(),text)+"\n<!-- widgets -->")
        # send the email
	smtp.send("[myHouse] Alerts "+date,template.encode('utf-8'),[])

# main
if __name__ == '__main__':
	run()

