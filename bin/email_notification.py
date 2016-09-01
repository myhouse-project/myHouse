#!/usr/bin/python
import sys
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import generate_charts

run_generate_charts = True

# return the HTML template of the widget
def get_widget_template(tag,title):
	template = '<tr class="total" style="font-family: \'Helvetica Neue\',Helvetica,Arial,sans-serif; \
	box-sizing: border-box; font-size: 14px; margin: 0;"><td class="alignright" width="80%" style="font-family: \'Helvetica \
	Neue\',Helvetica,Arial,sans-serif; box-sizing: border-box; font-size: 14px; vertical-align: top; text-align: center; border-top-width: 2px; \
	border-top-color: #333; border-top-style: solid; border-bottom-color: #333; border-bottom-width: 2px; border-bottom-style: solid; font-weight: 700; \
	margin: 0; padding: 5px 0;" valign="top">!title! \
	<br><img src="cid:!tag!"/> \
	</td></tr>'
	template = template.replace("!tag!",tag)
	template = template.replace("!title!",title)
	return template

# attach the image to the given message
def attach_image(msg,tag):
        with open(conf['constants']['charts_directory']+'/'+tag+'.png', 'r') as chart:
                img = MIMEImage(chart.read())
                chart.close()
                img.add_header('Content-ID', '<{}>'.format(tag))
                msg.attach(img)

# send out the email notification
def run(module_id):
	if run_generate_charts: generate_charts.run(module_id)
	date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	# load and prepare the template
	msg = MIMEMultipart()
        with open(conf['constants']['email_template'], 'r') as file:
                template = file.read()
        template = template.replace("!date!",date)
        template = template.replace("!url!",conf['web']['url'])
	template = template.replace("!version!",conf['constants']['version_string'])
	module = utils.get_module(module_id)
	template = template.replace("!module!",module['display_name'])
	
        if 'sensor_groups' in module:
	        # for each group
	        for i in range(len(module["sensor_groups"])):
	        	group = module["sensor_groups"][i]
	               	for j in range(len(group["widgets"])):
				# for each widget add it to the template
	                        widget = group["widgets"][j];
				tag = module_id+"_"+group["group_id"]+"_"+widget["widget_id"]
				template = template.replace("<!-- widgets -->",get_widget_template(tag,'')+"\n<!-- widgets -->")
				# attach the image to the message
				attach_image(msg,tag)
        # send the email
        msg['From'] = conf["email"]["from"]
        msg['To'] = ", ".join(conf["email"]["to"])
        msg['Subject'] = "[myHouse] "+module['display_name']+" Report "+date
        msg.attach(MIMEText(template, 'html'))
	smtp = smtplib.SMTP(conf["email"]["hostname"])
	smtp.sendmail(conf["email"]["from"],conf["email"]["to"], msg.as_string())
        smtp.quit()

# main
if __name__ == '__main__':
        if (len(sys.argv) != 2): print "Usage: email_notification.py <module_id>"
        else: run(sys.argv[1])

