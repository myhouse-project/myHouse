#!/usr/bin/python
from flask import Flask,request,send_from_directory,render_template,current_app
import logging
import json

import utils
import sensors
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
@app.route('/config')
def get_config():
	return config.get_json_config()

# return the latest read of a sensor
@app.route('/<module>/sensors/<group_id>/<sensor_id>/current')
def sensor_get_current(module,group_id,sensor_id):
	return json.dumps(sensors.web_get_current(module,group_id,sensor_id))

# return the time difference between now and the latest measure
@app.route('/<module>/sensors/<group_id>/<sensor_id>/timestamp')
def sensor_get_current_timestamp(module,group_id,sensor_id):
        return json.dumps(sensors.web_get_current_timestamp(module,group_id,sensor_id))


# return the data of a requested sensor based on the timeframe and stat requested
@app.route('/<module>/sensors/<group_id>/<sensor_id>/<timeframe>/<stat>')
def sensor_get_data(module,group_id,sensor_id,timeframe,stat):
	return json.dumps(sensors.web_get_data(module,group_id,sensor_id,timeframe,stat))

# run the web server
def run():
	# configure logging
	web_logger = logging.getLogger('werkzeug')
	web_logger.setLevel(conf["logging"]["level"]["scheduler"])
	web_logger.addHandler(logger.get_file_logger(conf["logging"]["level"]["scheduler"],conf["constants"]["logging"]["path"]+"web.log"))
	# run the application
	log.info("Starting web server on port "+str(conf["web"]["port"]))
        app.run(debug=True, use_reloader=conf["web"]["use_reloader"], host='0.0.0.0',port=conf["web"]["port"])

# run the main web app
if __name__ == '__main__':
        run()

