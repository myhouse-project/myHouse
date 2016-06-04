from flask import Flask,request,send_from_directory,render_template
import redis
import time
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/weather")
import weather_frontend

app = Flask(__name__,template_folder='static/templates')

debug = 0

# read global settings
config = {}
execfile(os.path.abspath(os.path.dirname(__file__))+"/conf/myHouse.py", config)
if (config["debug"]): debug = 1

# static HTML files
@app.route('/')
def web_root():
	return render_template("index.html")

@app.route('/static/<path:filename>')
def web_static(filename):
	return send_from_directory("static", filename)

## WEATHER MODULE
# webcams
@app.route('/weather/static/webcams')
def weather_webcams():
	return weather_frontend.webcams()

# forecast
@app.route('/weather/<query>')
def weather_query(query):
	return weather_frontend.query(request,query)

# weather data
@app.route('/weather/<sensor_name>/<sensor_measure>/<timeframe>')
def weather_data(sensor_name,sensor_measure,timeframe):
	return weather_frontend.data(request,sensor_name,sensor_measure,timeframe)

# run the main web app
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0',port=80)
