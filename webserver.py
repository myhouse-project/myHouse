#!/usr/bin/python
from flask import Flask,request,send_from_directory,render_template,current_app
from flask_compress import Compress
from flask import Response
import logging
import sys
import json

import utils
import sensors
import db
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import alerter

# define the web application
app = Flask(__name__,template_folder=conf["constants"]["base_dir"])
# apply gzip compression 
if conf["gui"]["compress"]: Compress(app)

# render index if no page name is provided
@app.route('/')
def root():
	return render_template(conf["constants"]["web_template"])

# return favicon
@app.route('/favicon.ico')
def favicon():
	return send_from_directory(conf["constants"]["web_dir"],"favicon.ico")

# static folder (web)
@app.route('/web/<path:filename>')
def static_page(filename):
	return send_from_directory(conf["constants"]["web_dir"], filename)

# return the json config
@app.route('/config')
def get_config():
	return config.get_json_config()

# save a configuration file
@app.route('/save_config',methods = ['POST'])
def save_config():
	return config.save(request.form["configuration"])

# restart the service
@app.route('/restart')
def restart():
	log.info("Restarting the service...")
	shutdown_server()
	utils.run_command(conf['constants']['service_location']+" restart")
	sys.exit(0)

# return the internet status
@app.route('/internet_status')
def get_internet_status():
	return utils.web_get("http://ipinfo.io")

# return the latest read of a sensor
@app.route('/<module_id>/<group_id>/<sensor_id>/current')
def sensor_get_current(module_id,group_id,sensor_id):
	# can return an image or text, set the correct content type
	content_type = "text/html"
	sensor = utils.get_sensor(module_id,group_id,sensor_id)
	if sensor is not None and sensor["format"] == "image": content_type = "image"
	return Response(sensors.data_get_current(module_id,group_id,sensor_id), mimetype=content_type)

# return a calendar's configuratio
@app.route('/<module_id>/<group_id>/<sensor_id>/calendar')
def sensor_get_calendar(module_id,group_id,sensor_id):
	return sensors.data_get_calendar(module_id,group_id,sensor_id)

# return the latest image of a sensor
@app.route('/<module_id>/<group_id>/<sensor_id>/image')
def sensor_get_current_image(module_id,group_id,sensor_id):
	night_day = True if request.args.get('night_day') else False
	return sensors.data_get_current_image(module_id,group_id,sensor_id,night_day)

# return the time difference between now and the latest measure
@app.route('/<module_id>/<group_id>/<sensor_id>/timestamp')
def sensor_get_current_timestamp(module_id,group_id,sensor_id):
	return sensors.data_get_current_timestamp(module_id,group_id,sensor_id)

# return the data of a requested sensor based on the timeframe and stat requested
@app.route('/<module_id>/<group_id>/<sensor_id>/<timeframe>/<stat>')
def sensor_get_data(module_id,group_id,sensor_id,timeframe,stat):
	return sensors.data_get_data(module_id,group_id,sensor_id,timeframe,stat)

# set the value of an input sensor
@app.route('/<module_id>/<group_id>/<sensor_id>/set/<value>',methods = ['GET', 'POST'])
def sensor_set(module_id,group_id,sensor_id,value):
	if request.method == 'POST': value = request.form["value"]
	return sensors.data_set(module_id,group_id,sensor_id,value)

# send a message to a sensor
@app.route('/<module_id>/<group_id>/<sensor_id>/send/<value>')
def sensor_send(module_id,group_id,sensor_id,value):
	force = True if request.args.get('force') is not None else False
	return sensors.data_send(module_id,group_id,sensor_id,value,force=force)

# read or save the measure of a given sensor
@app.route('/<module_id>/<group_id>/<sensor_id>/run/<action>')
def sensor_run(module_id,group_id,sensor_id,action):
	return sensors.data_run(module_id,group_id,sensor_id,action)

# return the alerts
@app.route('/alerts/<severity>/<timeframe>')
def alerts_get_data(severity,timeframe):
	return alerter.data_get_alerts(severity,timeframe)

# handle errors
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(Exception)
def error(error):
	message = request.path+": "+str(error)
	log.warning(message)
	return message

# shutdown the web server
def shutdown_server():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()

# run the web server
def run():
	# configure logging
	logger_name = "webserver"
	web_logger = logging.getLogger('werkzeug')
	web_logger.setLevel(logger.get_level(conf["logging"][logger_name]["level"]))
	web_logger.addHandler(logger.get_file_logger(logger_name))
	# run the application
	log.info("Starting web server on port "+str(conf["gui"]["port"]))
	app.run(debug=True, use_reloader=conf["constants"]["web_use_reloader"], host='0.0.0.0',port=conf["gui"]["port"])

# run the main web app
if __name__ == '__main__':
	run()

