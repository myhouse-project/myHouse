#!/usr/bin/python
from flask import Flask,request,send_from_directory,render_template,current_app
import logging

import utils
import logger
import config
log = logger.get_logger(__name__)
config = config.get_config()

app = Flask(__name__,template_folder='static/templates')


# static HTML files
@app.route('/')
def web_root():
        return render_template("index.html")

@app.route('/static/<path:filename>')
def web_static(filename):
        return send_from_directory("static", filename)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown')
def shutdown():
	return "OK"
	log.info('webserver shutting down...')
	shutdown_server()


def run():
	weblog = logging.getLogger('werkzeug')
	weblog.setLevel(logging.DEBUG)
        file = logging.FileHandler(logger.get_log_path()+"web.log")
        file.setLevel(logging.DEBUG)
        file.setFormatter(logger.formatter)
	weblog.addHandler(file)
        app.run(debug=False, host='0.0.0.0',port=config["web"]["port"])




# run the main web app
if __name__ == '__main__':
        run()

