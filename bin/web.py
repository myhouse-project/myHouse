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

@app.route('/sensors/<module>/<group_id>/<sensor_id>')
def sensor_latest(module,group_id,sensor_id):
	key = constants.db_schema["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
	# return the latest measure
	return json.dumps(db.range(key,withscores=False,milliseconds=True))

@app.route('/sensors/<module>/<group_id>/<sensor_id>/<timeframe>/<stat>')
def sensor_data(module,group_id,sensor_id,timeframe,stat):
        key = constants.db_schema["root"]+":"+module+":sensors:"+group_id+":"+sensor_id
        if timeframe == "recent":
		# recent hourly measures up to now
		key = key+":hour:"+stat
                start = utils.recent()
		end = utils.now()
		withscores = False
        elif timeframe == "history":
		# historical daily measures up to new
		key = key+":day:"+stat
                start = utils.history()
		end = utils.now()
		withscores = True
	elif timeframe == "today":
		# today's measure
		key = key+":day:"+stat
		start = utils.day_start(utils.now())
		end = utils.day_end(utils.now())
		withscores = False
        elif timeframe == "yesterday":
		# yesterday's measure
                key = key+":day:"+stat
                start = utils.day_start(utils.yesterday())
                end = utils.day_end(utils.yesterday())
                withscores = False
        else: return json.dumps([])
        return json.dumps(db.rangebyscore(key,start,end,withscores=withscores,milliseconds=True))



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

