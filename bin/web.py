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

@app.route('/<module>/sensors/<sensor_id>/<measure>/range/<timeframe>')
def sensor_range(module,sensor_id,measure,timeframe):
	key = constants.db_schema["root"]+":"+module+":sensors:"+sensor_id+":"+measure
	if timeframe == "today":
		data = db.rangebyscore(key+":hour:avg",utils.last_day_end(),utils.now(),withscores=False)
		min = utils.min(data)
		max = utils.max(data)
	elif timeframe == "yesterday":
		min = db.range(key+":day:min",withscores=False)
		max = db.range(key+":day:max",withscores=False)
	else: 
		min = db.range(key+":min",withscores=False)
		max = db.range(key+":max",withscores=False)
	return json.dumps([min,max])

@app.route('/<module>/sensors/<sensor_id>/<measure>/current')
def sensor_current(module,sensor_id,measure):
	key = constants.db_schema["root"]+":"+module+":sensors:"+sensor_id+":"+measure
	return json.dumps(db.range(key))

@app.route('/<module>/sensors/<sensor_id>/<measure>/data/<timeframe>')
def sensor_data(module,sensor_id,measure,timeframe):
	key = constants.db_schema["root"]+":"+module+":sensors:"+sensor_id+":"+measure
	if timeframe == "recent": 
		start = utils.recent()
		key = key+":hour:avg"
	elif timeframe == "history": 
		start = utils.history()
		key = key+":day:avg"
	else: start = utils.recent()
	end = utils.now()
	return json.dumps(db.rangebyscore(key,start,end))


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

