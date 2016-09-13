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

# variables
initialized = False
connected = False
slack = None
bot_id = None
channel_id = None
bot_name = conf["notification"]["slack"]["bot_name"]
channel_name = conf["notification"]["slack"]["channel"]

# says something to the channel
def says(text,channel=None):
	init()
	if not initialized: return
	if channel is None: channel = channel_id
	log.info("saying: "+text)
	slack.api_call("chat.postMessage", channel=channel,text=text, as_user=True)	

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
	slack = SlackClient(conf["notification"]["slack"]["bot_token"])
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

# attach the bot to the channel
def run():
	init()
	if not initialized: return
	# connect to the RTM API
	if slack.rtm_connect():
		log.info("bot "+bot_name+" online")
		while True:
			# read a rtm stream
			output_list = slack.rtm_read()
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
						response = oracle.ask(request)
						slack.api_call("chat.postMessage", channel=channel,text=response, as_user=True)
			time.sleep(1)
	else:
		log.error("unable to connect to the slack server")

# main
if __name__ == '__main__':
	run()


