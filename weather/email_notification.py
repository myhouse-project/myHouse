import generate_charts
import os
import sys
import requests
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# configuration settings
debug = 0
run_generate_charts = 1
send_email = 1
charts_directory = os.path.abspath(os.path.dirname(__file__))+"/charts";

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/../conf/myHouse.py", config)
if (config["debug"]): debug = 1

# main
def main():
	date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'(%B %e, %Y)')
	# generate all the charts
	if run_generate_charts: generate_charts.main()
	msg = MIMEMultipart()
	# load and prepare the template
	with open(os.path.abspath(os.path.dirname(__file__))+"/email_template.html", 'r') as file:
		template = file.read()
	template = template.replace("!date!",date);
	template = template.replace("!website!",config["website"]);
	# retrieve the forecast
	try: 
		forecast = requests.get(config["website"]+'weather/forecast').json()
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)
	entry = forecast["forecast"]["simpleforecast"]["forecastday"][0]
	description = entry["conditions"]+'. ';
	if (entry["pop"] > 0): description = description + 'Precip. '+str(entry["pop"])+'%. ';
	if (entry["qpf_allday"]["mm"] > 0): description = description + 'Rain '+str(entry["qpf_allday"]["mm"])+' mm. ';
	if (entry["snow_allday"]["cm"] > 0): description = description + 'Snow '+str(entry["snow_allday"]["cm"])+' cm. ';
	attach_image(msg,"forecast",charts_directory+"/../../static/weather-icons/"+str(entry["icon"])+".png")
	template = template.replace("!forecast!",description+"<br>("+str(entry["low"]["celsius"])+"&deg;C -"+str(entry["high"]["celsius"])+"&deg;C)");
	# attach the images
	attach_image(msg,"almanac_outdoor",charts_directory+"/"+"almanac_outdoor.png")
	attach_image(msg,"almanac_indoor",charts_directory+"/"+"almanac_indoor.png")
	attach_image(msg,"recent_outdoor",charts_directory+"/"+"recent_outdoor.png")
	attach_image(msg,"recent_indoor",charts_directory+"/"+"recent_indoor.png")
	attach_image(msg,"history_outdoor",charts_directory+"/"+"history_outdoor.png")
	attach_image(msg,"history_indoor",charts_directory+"/"+"history_indoor.png")
	# send the email
	msg['From'] = config["email_from"]
	msg['To'] = ", ".join(config["email_to"])
	msg['Subject'] = "Weather Report "+date
	msg.attach(MIMEText(template, 'html'))
	try:
		if send_email: 
			s = smtplib.SMTP(config["email_server"])
			s.sendmail(config["email_from"],config["email_to"], msg.as_string())
			s.quit()
	except Exception as e: 
		print "ERROR: "+str(e)
		sys.exit(1)

# attach the image to the given message
def attach_image(msg,cid,filename):
	with open(filename, 'r') as chart:
		img = MIMEImage(chart.read())
		chart.close()
		img.add_header('Content-ID', '<{}>'.format(cid))
		msg.attach(img)
		
# main
if __name__ == '__main__':
	module=0
	main()
