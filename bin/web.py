#!/usr/bin/python
from flask import Flask,request,send_from_directory,render_template,current_app
import logging

import utils
import constants
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
def web_config():
	return config.get_json_config()

# run the web server
def run():
	# configure logging
	web_logger = logging.getLogger('werkzeug')
	web_logger.setLevel(conf["logging"]["level"])
	web_logger.addHandler(logger.get_file_logger(conf["logging"]["level"],constants.log_path+"web.log"))
	# run the application
	log.info("Starting web server on port "+str(conf["web"]["port"]))
        app.run(debug=True, use_reloader=False, host='0.0.0.0',port=conf["web"]["port"])

# run the main web app
if __name__ == '__main__':
        run()

