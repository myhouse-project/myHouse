#!/usr/bin/python
import datetime
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import utils
import logger
import db
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import generate_charts
import smtp

# variables
run_generate_charts = True

# return the HTML template of the widget
def get_email_widget(title,body):
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

# return the email HTML template
def get_email_body(title):
        with open(conf['constants']['email_template'], 'r') as file:
                template = file.read()
        template = template.replace("#url#",conf['web']['url'])
        template = template.replace("#version#",conf['constants']['version_string'])
        template = template.replace("#title#",title)
	return template

# email module digest
def module_digest(requested_module):
	module_id = requested_module
	log.info("generating module summary email report for module "+module_id)
	module = utils.get_module(module_id)
	if module is None: return
	images = []
	if run_generate_charts: generate_charts.run(module_id)
	date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	title = module['display_name']+" Report "+date
	template = get_email_body(title)
	if 'widgets' not in module: return
	# for each widget
        for i in range(len(module["widgets"])):
		for j in range(len(module["widgets"][i])):
			widget = module["widgets"][i][j]
			if "module" in widget: module_id = widget["module"]
	        	group = utils.get_group(module_id,widget["sensor_group"])
                        if group is None:
                                log.warning("["+requested_module+"] invalid group "+widget["sensor_group"]+" for widget "+widget["widget_id"])
                                continue
			template = template.replace("<!-- widgets -->",get_email_widget('','<img src="cid:'+widget["widget_id"]+'"/>')+"\n<!-- widgets -->")
			# add the image to the queue
			images.append({'filename': utils.get_widget_chart(widget["widget_id"]) , 'id': widget["widget_id"],})
        # send the email
	smtp.send(title,template,images)

# email alert digest
def alerts_digest():
        log.info("generating alerts summary email report")
        alerts = ['alert','warning','info']
        date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	title = "Alerts Summary "+date
	template = get_email_body(title)
        for severity in alerts:
                # for each severity, get the data
                text = ""
		data = db.rangebyscore(conf["constants"]["db_schema"]["alerts"]+":"+severity,utils.recent(),utils.now(),withscores=True,milliseconds=True)
                if len(data) == 0: continue
                # merge the alerts together
                for alert in data:
                        text = "<small>* "+alert[1]+" *</small><br>"+text
                template = template.replace("<!-- widgets -->",get_email_widget(severity.capitalize(),text)+"\n<!-- widgets -->")
        # send the email
        smtp.send(title,template.encode('utf-8'),[])

# email realtime alert
def alert(text):
        log.info("emailing alert "+text)
        title = "Alert!"
        template = get_email_body(title)
	template = template.replace("<!-- widgets -->",get_email_widget("Alert",text))
        # send the email
        smtp.send(title,template.encode('utf-8'),[])

