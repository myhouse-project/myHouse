myHouse
=======================
Modular home automation suite, suitable for Raspberry Pi.

Modules
-----------------
- Weather: 
	- Measure and display indoor (through ds18b20 sensors) and outdoor (from wunderground) temperatures
	- Display a 6-days weather forecast (from wunderground)
	- Display rain-related alerts (from Weather Channel)
	- Display four configurable webcams
	- Keep track and display by hour and day the following: min/max temperature, average temperature, min/max record temperature, weather condition
	- Send by email a daily weather report

Requirements
-----------------
- Linux/Unix
- python
- redis
- python-flask
- Browser

Installation
-----------------
- Install the required dependences
- Unzip the package and copy the folder to a directory of choice (e.g. /opt/myHouse)
- Rename conf/myHouse.template.py into conf/myHouse.py
- Review the configuration settings in myHouse.py
- Copy the content of the file docs/crontab and add it to your crontab (crontab -e)
- Run the web interface (sudo python main.py)

Usage 
-----------------
- Access the web interface on port 80
- A weather report summary is generated and sent by email every day

Known Issues
-----------------
- Temperatures are in Celsius only