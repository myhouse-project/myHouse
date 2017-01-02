#!/usr/bin/python
import json
import time
from slackclient import SlackClient

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import oracle
import generate_charts

# variables
initialized = False
connected = False
slack = None
bot_id = None
channel_id = None
bot_name = conf["output"]["slack"]["bot_name"]
channel_name = conf["output"]["slack"]["channel"]
sleep_on_error = 1*60

# says something to the channel
def notify(text,channel=None):
	init()
	if not initialized: return
	if channel is None: channel = channel_id
	log.debug("saying: "+text)
	slack_message(channel,text)

# return the ID corresponding to the bot name
def get_user_id(username):
	users = slack.api_call("users.list")
	if not users.get('ok'): return None
	users = users.get('members')
	for user in users:
        	if 'name' in user and user.get('name') == username: return user.get('id')
	return None

# return the ID corresponding to the channel name
def get_channel_id(channelname):
	channels = slack.api_call("channels.list")
	if not channels.get('ok'): return None
	channels = channels.get('channels')
	for channel in channels:
		if 'name' in channel and channel.get('name') == channelname: return channel.get('id')
	return None

# initialize the integration
def init():
	global slack
        global bot_id
        global channel_id
	global initialized
	if initialized: return
	log.info("Initializing slack...")
	# initialize the library
	try:
		# initialize the library
		slack = SlackClient(conf["output"]["slack"]["bot_token"])
		# test the authentication
		auth = slack.api_call("auth.test")
		if not auth["ok"]:
			log.error("authentication failed: "+auth["error"])
			return 
	        # retrieve the bot id
	        global bot_id
	        bot_id = get_user_id(bot_name)
	        if bot_id is None:
	                log.error("unable to find your bot "+bot_name+". Ensure it is configured correctly")
	                return
	        # retrieve the channel id
	        global channel_id
	        channel_id = get_channel_id(channel_name)
	        if channel_id is None:
	                log.error("unable to find the channel "+channel_name)
	                return 
		initialized = True
        except Exception,e:
                log.warning("unable to initialize slack: "+utils.get_exception(e))

# connect to the RTM API
def connect():
	global connected
	if connected: return
        if slack.rtm_connect():
                log.info("slack bot online ("+bot_name+")")
		connected = True
		return
	log.error("unable to connect to slack")

# send a message to slack
def slack_message(channel,message):
	try:
		slack.api_call("chat.postMessage",channel=channel,text=message,as_user=True)	
	except Exception,e:
        	log.warning("unable to post message to slack: "+utils.get_exception(e))

# send a file to slack
def slack_upload(channel,filename):
	try:
		slack.api_call("files.upload",channels=channel,filename=filename,file=open(filename,'rb'))
        except Exception,e:
                log.warning("unable to upload file to slack: "+utils.get_exception(e))

# attach the bot to the channel
def run():
	global initialized, connected
	while True:
		# init slack
	        init()
        	if not initialized: time.sleep(sleep_on_error)
		# connect to slack
		connect()
		if not connected: time.sleep(sleep_on_error)
		# read a rtm stream
		try: 
			output_list = slack.rtm_read()
        	except Exception,e:
	                log.warning("unable to read from slack: "+utils.get_exception(e))
			initialized = False
			connected = False
			time.sleep(sleep_on_error)
		if output_list and len(output_list) > 0:
			for output in output_list:
				if not output or 'text' not in output: continue
				if output['user'] == bot_id: continue
				# for each output
				if bot_id in output['text'] or bot_name in output['text'] or output['channel'].startswith("D"):
					# if the message is to the bot
					request = output['text']
					request = request.replace(bot_name,'')
					request = request.replace(bot_id,'')
					request = request.lower()
					channel = output['channel']
					# ask the oracle what to respond
					response = oracle.ask(request)
					if response["type"] == "text":
						# post the text response
						slack_message(channel,response["content"])
					elif response["type"] == "chart":
						# post a waiting message
						slack_message(channel,oracle.get_wait_message())
						# generate the chart
						module_id,widget_id = response["content"].split(",")
						try: 
							widgets = generate_charts.run(module_id,widget_id)
						except Exception,e:
							log.warning("unable to generate the chart for "+module_id+":"+widget_id+": "+utils.get_exception(e))
							continue
						# upload the chart to the channel
						if len(widgets) > 0:
							filename = utils.get_widget_chart(widgets[0])
							log.debug("uploading "+filename)
							slack_upload(channel,filename)
						else: slack_message(channel,"unable to find the chart "+filename)
		time.sleep(1)

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		run()
	else:
		notify(sys.argv[1])		
	
