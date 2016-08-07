#!/usr/bin/python
from flask import Flask,request,send_from_directory,render_template,current_app
import logging
import json

import utils
import constants
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# define the web application
app = Flask(__name__,template_folder='../web/templates')

# render index if no page name is provided
@app.route('/')
def web_root():
        return render_template("index.html")

# static folder (web)
@app.route('/web/<path:filename>')
def web_static(filename):
        return send_from_directory("../web", filename)

# shutdown the server
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    func()

@app.route('/shutdown')
def shutdown():
	return "OK"
	log.info('webserver shutting down...')
	shutdown_server()

# return the json config
@app.route('/get_config')
def get_config():
	return config.get_json_config()

@app.route('/sensors/<module>/<group_id>/<sensor_id>/range/<timeframe>')
def sensor_range(module,group_id,sensor_id,timeframe):
	key = constants.db_schema["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
	min = max = None
	if timeframe == "today":
		# for today min and max need to be calculated on the fly
		data = db.rangebyscore(key+":hour:avg",utils.day_start(utils.now()),utils.now(),withscores=False,milliseconds=True)
		min = utils.min(data)
		max = utils.max(data)
	elif timeframe == "yesterday":
		# for yesterday min and max have already been calculated
		min_data = db.rangebyscore(key+":day:min",utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()),withscores=False,milliseconds=True)
		max_data = db.rangebyscore(key+":day:max",utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()),withscores=False,milliseconds=True)
		if len(min_data) > 0: min = min_data[0]
		if len(max_data) > 0: max = max_data[0]
	else: 
		min_data = db.rangebyscore(key+":min",utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()),withscores=False,milliseconds=True)
		max_data = db.rangebyscore(key+":max",utils.day_start(utils.yesterday()),utils.day_end(utils.yesterday()),withscores=False,milliseconds=True)
                if len(min_data) > 0: min = min_data[0]
                if len(max_data) > 0: max = max_data[0]
	return json.dumps([min,max])

@app.route('/sensors/<module>/<group_id>/<sensor_id>/current')
def sensor_current(module,group_id,sensor_id):
	key = constants.db_schema["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
	# return the latest measure
	return json.dumps(db.range(key,milliseconds=True))

@app.route('/sensors/<module>/<group_id>/<sensor_id>/data/<timeframe>/<stat>')
def sensor_data(module,group_id,sensor_id,timeframe,stat):
	key = constants.db_schema["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
	if timeframe == "recent": 
		# start from the recent timestamp
		start = utils.recent()
		# retrieve the hourly measures
		key = key+":hour:"+stat
	elif timeframe == "history": 
		# start from the history timestamp
		start = utils.history()
		# retrieve the daily measures
		key = key+":day:"+stat
	else: return json.dumps([])
	end = utils.now()
	return json.dumps(db.rangebyscore(key,start,end,milliseconds=True))


# run the web server
def run():
	# configure logging
	web_logger = logging.getLogger('werkzeug')
	web_logger.setLevel(conf["logging"]["level"]["scheduler"])
	web_logger.addHandler(logger.get_file_logger(conf["logging"]["level"]["scheduler"],constants.log_path+"web.log"))
	# run the application
	log.info("Starting web server on port "+str(conf["web"]["port"]))
        app.run(debug=True, use_reloader=conf["web"]["use_reloader"], host='0.0.0.0',port=conf["web"]["port"])

# run the main web app
if __name__ == '__main__':
        run()

