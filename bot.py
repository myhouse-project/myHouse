#!/usr/bin/python
import json
import time
from slackclient import SlackClient

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
slack = SlackClient(conf["slack"]["bot_token"])
bot_id = None
channel_id = None

# return the ID corresponding to the bot name
def get_bot_id():
	users = slack.api_call("users.list")
	if not users.get('ok'): return None
	users = users.get('members')
	for user in users:
        	if 'name' in user and user.get('name') == conf["slack"]["bot_name"]: return user.get('id')
	return None

# return the ID corresponding to the channel name
def get_channel_id():
	channels = slack.api_call("channels.list")
	if not channels.get('ok'): return None
	channels = channels.get('channels')
	for channel in channels:
		if 'name' in channel and channel.get('name') == conf["slack"]["channel"]: return channel.get('id')
	return None

def handle_command(command, channel):
	response = "Not sure what you mean. Use the command with numbers, delimited by spaces."
	if command.startswith("do"):
		response = "Sure...write some more code then I can do that!"
	slack.api_call("chat.postMessage", channel=channel,text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and bot_id in output['text']:
		                return output['text'].split(bot_id)[1].strip().lower(),output['channel']
	return None, None

def run():
	# retrieve the bot id
	global bot_id
	bot_id = get_bot_id()
	if bot_id is None: return
	print "Bot ID: "+bot_id
	# retrieve the channel id
	global channel_id
        channel_id = get_channel_id()
        if channel_id is None: return
        print "Channel ID: "+channel_id
	if slack.rtm_connect():
		print("StarterBot connected and running!")
		while True:
			command, channel = parse_slack_output(slack.rtm_read())
			if command and channel:
				handle_command(command, channel)
			time.sleep(5)
	else:
        	print("Connection failed. Invalid Slack token or bot ID?")


run()
