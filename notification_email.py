#!/usr/bin/python
import datetime
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import utils
import logger
import db
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import generate_charts

# variables
run_generate_charts = True

# attach the image to the given message
def attach_image(msg,image):
        with open(image['filename'], 'r') as file:
                img = MIMEImage(file.read(),_subtype="png")
                file.close()
                img.add_header('Content-ID', '<{}>'.format(image['id']))
                msg.attach(img)

# send an email
def send(subject,body,images=[]):
        msg = MIMEMultipart()
        # attach images
        if len(images) > 0:
                for image in images: attach_image(msg,image)
        # prepare the message
        msg['From'] = conf["output"]["email"]["from"]
        msg['To'] = ", ".join(conf["output"]["email"]["to"])
        msg['Subject'] = "[myHouse] "+subject
        msg.attach(MIMEText(body, 'html'))
        smtp = smtplib.SMTP(conf["output"]["email"]["hostname"])
        # send it
        log.info("sending email '"+subject+"' to "+msg['To'])
        smtp.sendmail(conf["output"]["email"]["from"],conf["output"]["email"]["to"], msg.as_string())
        smtp.quit()

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
        template = template.replace("#url#",conf['gui']['url'])
        template = template.replace("#version#",conf['constants']['version_string'])
        template = template.replace("#title#",title)
	return template

# email module digest
def module_digest(module_id):
	log.info("generating module summary email report for module "+module_id)
	images = []
	widgets = []
	module = utils.get_module(module_id)
	if module is None: return
	if run_generate_charts: widgets = generate_charts.run(module_id,generate_chart=run_generate_charts)
	date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	title = module['display_name']+" Report "+date
	template = get_email_body(title)
	if 'widgets' not in module: return
	# for each widget
	for widget_id in widgets:
		template = template.replace("<!-- widgets -->",get_email_widget('','<img src="cid:'+widget_id+'"/>')+"\n<!-- widgets -->")
		# add the image to the queue
		images.append({'filename': utils.get_widget_chart(widget_id),'id': widget_id,})
        # send the email
	send(title,template,images)

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
		data = db.rangebyscore(conf["constants"]["db_schema"]["alerts"]+":"+severity,utils.recent(),utils.now(),withscores=True,format_date=True)
                if len(data) == 0: continue
                # merge the alerts together
                for alert in data:
                        text = "<small>["+alert[0]+"] "+alert[1]+"</small><br>"+text
                template = template.replace("<!-- widgets -->",get_email_widget(severity.capitalize(),text)+"\n<!-- widgets -->")
        # send the email
        send(title,template.encode('utf-8'),[])

# email realtime alert
def notify(text):
        log.info("emailing alert "+text)
        title = "Alert!"
        template = get_email_body(title)
	template = template.replace("<!-- widgets -->",get_email_widget("Alert",text))
        # send the email
        send(title,template.encode('utf-8'),[])

# main
if __name__ == '__main__':
        if len(sys.argv) == 1:
		print "Usage: "+__file__+" <module_id>"
	else:
		module_digest(sys.argv[1])
