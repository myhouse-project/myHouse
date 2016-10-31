==============
myHouse
==============
Home monitoring and automation suite for Raspberry Pi

Features
===========
- Collect data from a number of sensors by leveraging a simple to customize plugin-based architecture
- Automatic calculation of hourly and daily minimum/maximum/average values for each sensor
- Fully customizable web interface with mobile support to display the sensors' statistics, control actuators and present custom data
- Natural-language interactive Slack bot for remotely retrieving any statistic, send commands or just having fun
- Alerting module generating e-mails or Slack notifications whenever a configured condition is met
- Daily e-mail digests embedding all the widgets configured for the requeted module

How it works 
===========
Think of myHouse as a framework for automating your house. The first step is to **configure the sensors** you want to collect data from. Included in the package, there are already a number of plugins (e.g. to collect weather statistics, information from the linux box when it runs, retrieving images from the Internet, your GPS position from icloud, data collected by Wirelessthings/Ciseco sensors, etc.) and you can easily add your own plugins.
Once your sensors are configured and data has been collecting, the suite automatically calculates for every hour and for every day minimum/maximum/average values so to present only summarized information without overloading with unnecessary data.

What will be presented in the web interface is completely up to you. You can **define your own modules**, chose your icons and **configure all the widgets** that will be presented in the order you like the most. The statistics elaborated by the tool can be presented in a number of ways: timeline charts for different group of sensors with recent or historical data, current measures and minimum/maximum values for today and yesterday are just some of the examples. From the interface your **actuators can be controlled** as well: thanks to input fields, switches and a fully-featured scheduler, you can meet easily whatever requirements you might have.

Collecting and presenting statistics is nice but you may want to be automatically alerted whenever a specific situation is taking place. This is why you can easily **create rules** which will trigger when the set of conditions you have defined will be all true. Actions can be configured as well to e.g. send a message to an actuator or just set the value of a sensor. An alert does not necessarily represent a critical situation but can be just a simple messages (e.g. the minimum and maximum temperature we had yesterday indoor) to share with the users. Notifications are both presented within the web interface, sent by e-mail and posted on a Slack channel of your choice.

If you don't know what Slack is, have a look at it. This collaborative, real-time messaging tool can become your family's virtual place when enhanced by myHouse. Not only myHouse's **Slack bot will notify the members** when something is happening but allows **direct interaction in your natural language**. Depending on your questions and what the bot knows (e.g. the attached sensors and configured widgets), it can reply to your questions, share with you its charts and send commands to an actuator on your behalf. 

How I configured myHouse at home
---------------------------------------------------
Since myHouse is a framework, **everything is defined in the configuration file** so my instance may look completely different than yours. This is nice because **allows great flexibility but requires a starting point** if you don't want to get lost in the configuration. For this reason, I'm making **my own configuration part of the distribution** package: most of the modules and rules are disabled since do not necessarily work in your environment but at least you have a **fully working example** to take inspiration from.
In my own myHouse, I have configured the following **sensors**:

- Pressure, temperature, ambient light and humidity from Wirelessthings/Ciseco sensors
- Forecast, weather condition, temperature, wind, rain/snow from Weather Underground
- Weather alerts from Weather Channel
- GPS position of the family's members from icloud
- Snapshots from multiple indoor and outdoor webcams
- A number of system statistics from the raspberry pi hosting the application

I have configured then the following modules and **widgets**:

- Dashboard
	- A selection of the most interesting widgets from the other modules
- Outdoor:
	- Forecast of the next 5 days, temperature ranges, weather conditions, chance of rain and snow
	- External temperature summary with current weather condition, minimum/maximum of today, yesterday, record and normal temperatures
	- External temperature recent (with hourly minimum/average/maximum) and historical (with daily minimum/average/maximum) timeline with weather condition
	- Historical precipitation timeline
	- Wind current measure, summary of today/yesterday, recent and historical timeline charts
	- Humidity current measure, summary of today/yesterday, recent and historical timeline charts
	- Ambient Light current measure, summary of today/yesterday, recent and historical timeline charts
	- Pressure current measure, summary of today/yesterday, recent and historical timeline charts
- Indoor:
	- Internal temperature summary, minimum/maximum of today, yesterday for each room
	- Internal temperature recent (with hourly minimum/average/maximum) and historical (with daily minimum/average/maximum) timeline
	- Humidity current measure, summary of today/yesterday, recent and historical timeline charts
	- Fridge and refrigerator current temperature, summary of today/yesterday, recent and historical timeline charts
	- Battery status of the different sensors
- Webcams:
	- Internet webcams as well as webcams I have indoor and outdoor
- Where are we?
	- Map with the GPS location of all the members of the family automatically generated by leveraging the "Where is my iphone?" API
- Boiler
	- Boiler status, manual switch to power it on/off and target temperature to reach while on
	- Calendar to schedule when the boiler has to automatically turns on and off
- System Status:
	- CPU current measure, summary of today/yesterday, recent and historical timeline charts
	- Memory current measure, summary of today/yesterday, recent and historical timeline charts
	- System load current measure, summary of today/yesterday, recent and historical timeline charts
	- Network Connections and services current measure, summary of today/yesterday, recent and historical timeline charts
	- Raspberry's current temperature, summary of today/yesterday, recent and historical timeline charts
	- Database size current measure and historical timeline chart
- Local Network:
	- Dnsmasq DHCP current leases, static DNS and DHCP mapping (my raspberry acts as a DNS/DHCP server)
- Log Analysis:
	- Daily Logwatch output
- Logs:
	- myHouse logs and system logs
- Configuration:
	- myHouse configuration module

I have finally configured the following **rules**:

- Outdoor module:
    - Weather alerts
    - Yesterday maximum/minimum temperature above or below the record for that day or the expected normal temperature
    - Yesterday maximum/minimum/average temperature the lowest/highest of the last few days
    - Forecast weather for tomorrow
- Indoor module:
    - Yesterday maximum/minimum/average temperature the lowest/highest of the last few days
    - Temperature inside too high or too low
    - Fridge/Refrigerator temperature too high
    - Flood alert
- System module:
    - CPU utilization/System load/temperature too high
- Boiler module:
    - Turning the boiler on/off when scheduled, requested, or when the indoor temperature is too low/high

I have eventually configured a number of **rules without conditions** (that are used by the bot for its basic knowledge) reporting upon current weather conditions, temperature, boiler status, etc.

Installing
========
- Unzip the package and move its contents to a directory of your choice on your raspberry Pi (e.g. /opt/myHouse)
- Run the installation script as root (e.g. sudo /opt/myHouse/install.py) which will:
    - download and install all the required dependencies
    - create a service script, copy into /etc/init.d/myHouse and configured it to start at boot time
    - start the service
- Access the web interface (e.g. http://your-raspberry-pi.ip)

Uninstalling
-----------------
- Run as root the installation script with the "-u" parameter (e.g. sudo /opt/myHouse/install.py -u) which will:
    - stop the service
    - remove the service script from /etc/init.d/myHouse
The dependencies, the database and all the other files belonging to myHouse will NOT be deleted.
		
Upgrading
---------------
- From 1.x to 2.0:
    - There is no automatic way to migrate the configuration since its format has completely changed across the versions. 
        - Move your settings manually into the config.json file
    - Data can be migrated using the provided upgrade_2.0.py script. 
        - Open the file and edit the variables on top first. Select what you want to migrate (recent data, history, etc.), the source and target databases and where each database's key has to be migrated into
        - Please note the script will migrate the data into a new database, it will not upgrade the existing v1.x database

Configuring
==========
The entire configuration of the suite is within the **config.json** file, of course in a JSON format (http://www.json.org/). If the file does not exist, **config-example.json** will be used instead. It is highly recommended to copy config-example.json into config.json at the first use and customize the latter.
The configuration itself is pretty articulated this is why it is highly recommended to review the **config-schema.json file for a detailed explanation of the different options and combinations available**. Alternatively, the configuration editor available from within the web interface allows to build your own configuration graphically. Either way, the resulting file is checked against the schema to ensure the configuration is correct upon startup. A service restart (e.g. sudo /etc/init.d/myHouse restart) is required to apply any change.

The logic behind the configuration file is pretty simple: there is a generic configuration first (where the database is, what is the mailserver, which recipient to send notifications to, how to connect to Slack, what and where to log, etc.) followed by a number of custom modules. Each **module** is an entry in the menu of the web interface and has three main sections:

- **sensors**: array of sensors belonging to the module. Each sensor includes the following information:
	- a group ID, sensors belonging to the same group can be presented within the same widget
	- a data structure to instruct the plugin to retrieve the data for the sensor, including the polling interval
	- a set of chart series (highcharts properites) that will be used when representing the chart in the web interface
- **widgets**: array of rows and widgets to be presented when the user clicks on the module within the web interface. Each widget is described by:
	- a size (up to 12 "slots" are available for each row)
	- a layout, e.g. multiple components within the same widgeta. The most common components are:
		- sensor_group_summary: generate a chart with min/max for each sensor of the specified group for today and yesterday
		- image: add an image from a sensor
		- sensor_group_timeline: generate a chart with a timeline of the given timeframe for the sensors belonging to the given group
		- chart_short/chart_short_inverted: generate a chart with a limited size with the data from a single sensor
		- current: generate a header with the current measure of a sensor and an icon
		- alerts: generate a table with all the alerts generated by the platform
		- checkbox: generate a checkbox controlling the given sensor
		- input: add an input form controlling a given sensor
		- separator: add a line separator
		- configuration: add the configuration editor
		- calendar: add a graphical scheduler storing information in a given sensor
		- data: add raw data from a given sensor
		- table: add a table and format data from a given sensor
- **rules**: array of rules for notifying when a given condition is met. When no condition is specified, the rule will be used by the "oracle" for responding to interactive requests. Each rule is described by:
	- a set of definitions of the data that will be used within the conditions. Each definition extracts from the database one or more values from a given sensor (e.g. yesterday's average temperature as the latest value of the daily average measures of the outdoor sensor).
	- a set of conditions for comparing dataset defined in the definitions section. All the conditions must be true to have an alert triggering
	- a severity of the alert
	- an time interval for evaluating the conditions (e.g. daily, hourly, every minute, never, etc.)		
	- the text of the alert with placeholders from the definitions  which will be replaced by the current values

Plugins
-----------
There are two types of plugin supported by the software: pull (the sensor is pulled at regular time intervals) or push (the plugin is kept running and when a new measure is received, the main engine is notified). The following plugins are part of the distribution:

- wunderground: retrieve from Weather Underground the requested measure (e.g. temperature, pressure, weather condition, forecast, etc. review config-schema.json for the full list):
    - request a valid API key from https://www.wunderground.com/weather/api/
    - set the latitude/longitude in the global plugin configuration or within each plugin settings
- weatherchannel: retrieve from Weather Channel weather alerts:
    - set the latitude/longitude in the global plugin configuration or within each plugin settings
    - create a rule to be alerted when the latest weather alert is not empty
- messagebridge: listen for updates from Wirelessthings/ciseco sensors and read the measure of the configured node:
    - the is no polling interval to configure for this plugin since updates are sent real-time by the wirelessthings messagebridge component. 
    - it can also instruct Generic IO firmware to sleep when awake
    - can be used to send messages to a sensor
    - ensure messagebridge is running (https://github.com/WirelessThings/WirelessThings-LaunchPad)
- csv: parse a csv file
    - the current implementation is for parsing the CSV_MessageBridge.csv file from Wirelessthings messagebridge
    - it can be used as a template for parsing custom csv files
- image: retrive an image from a given url
    - basic HTTP authentication is supported
- icloud: retrive from icloud the location of an IOS device:
    - run python plugin_icloud.py --username=youricloudemail@email.com to configure the plugin and store the icloud password within the keystore first
    - if family sharing is set up (https://support.apple.com/en-us/HT201060) you will have visibility over all the devices
    - a list of devices to display can be configured
- linux: execute a command on the raspberry pi to poll a sensor:
    - it can be either a pre-defined measure (review the config-schema.json for the full list) or a custom command
    - can be used to poll sensors directly attached to the GPIO of the raspberry pi

"Push" plugins must implement a "run" method (which will be called at startup to keep the plugin running in background) and a "register" method (for registering suitable sensors against the plugin). When a new measure is available, it must call the "store" method of sensors.py to save the data.
"Pull" plugins must instead implement a "poll" method (to retrieve the raw data from the sensor) and a "parse" method (to parse the raw the data previously polled). The main engine will be responsible to periodically invoke poll and parse and hence storing the new measure. Raw data polled for different sensor will be cached so to prevent multiple concurrent retrieval of the same data.
Plugins implementing a "send" method can send messages to their supported actuators.

Configuring your Slack bot
---------------------------------------

- Create a dedicated Slack team for your family (https://slack.com/) or login to an existing one
- Create a new Slack bot user:
    - go to https://api.slack.com/bot-users 
    - click on "Creating a new bot user" from "Custom bot users"
    - give your bot a name (e.g. housebot)
    - select your bot icon
    - an API token will be generated for your, copy and paste it in the myHouse configuration
- Go back in the Slack interface and invite your newly created bot to the channels you like
- Interact with your Slack bot with a DM or by calling it out (e.g. @housebot, hi) in the channels it is in
- The bot is able to interact in your natural language so there are no predefined commands. Its knowledge comes from the following:
    - every rule defined in the configuration file which has no condition
    - every widget from which an image can be generated (e.g. a timeline chart)
    - the bot.txt file which maps some keywords to random answers for a basic, static interaction
- Based on the question the bot checks what possible answer contains most of the expected keywords and if confident enough it will reply accordingly.

About myHouse
=============

Why myHouse?
----------------------
There are thousands of home automation suites around and dozens of new solutions made available every single day. So why yet another piece of software? I may have very **peculiar requirements** but none of the products around had a good fit for me.

First, I didn't want to use a cloud-based service both for privacy reasons and because my Internet connection is not necessarily always on so I had the need to both **store and present data from within my network**. 

Secondarily, I need to **review the statistics collected mostly when I am not at home**: this is why I had to exclude all the solutions which are creating charts with all the raw data collected if I wanted to avoid high latency and mobile roaming charges. Much lighter and more resistant to spikes looked to me to calculate average/minimum/maximum values for each hour and for each day. 

I also wanted a way to **centralize in a single place both the sensors and the webcams**, independently of the source. This is why this plugin-based architecture: if you are collecting the external temperature from an Internet service and you add a sensor at home to do the same later, you want to keep the history and use the same presentation format. For the same reason I wanted to be **indipendent from the different standards and IoT vendors** around.

I also wanted to create something adapting easily to the **extreme flexibility** needed by this kind of solutions. This is why everything is defined in the configuration, the sensors you want to collect data from, the widgets to present in the web interface, the way you want each chart to be drawn.

I also have the need to receive when I'm not at home a very **detailed e-mail summary** containing the same information as I was browsing the web interface. 

For the same reason (and because I **dont' not want to expose the web interface over the Internet** so making the access via the VPN not very handy) I wrote the Slack bot. It allows me to immediate access any information I need in real-time, interact with the actuators (e.g. my boiler) quicker and remotely and, why not, having some fun by arguing with a real bot.

The last technical requirement I had was to make the solution as **lighter as possible** (hence Flask instead of Apache/PHP) and gentle with the SD card of my raspberry pi (hence Redis instead of other SQL databases).7

Need help?
----------------
- The documentation is available at the following location: https://sourceforge.net/p/my-house/wiki/
- Report any bug or feature request at the following location: https://sourceforge.net/p/my-house/tickets/
- Download the latest release from the following location: https://sourceforge.net/projects/my-house/files/

Third-party software
-----------------------------
myHouse makes use of the following third-party software components:

- Python for the entire backend, including the following libraries:
	- flask for the webserver (http://flask.pocoo.org/)
	- numpy for calculating the average out of an array of values (http://www.numpy.org/)
	- APScheduler for scheduling all the recurrent tasks (https://apscheduler.readthedocs.io/en/latest/)
	- slackclient for interacting with Slack (https://github.com/slackhq/python-slackclient)
	- simplejson for more detailed json syntax checks (https://simplejson.readthedocs.io/en/latest/)
	- fuzzywuzzy for fuzzy string matching (https://github.com/seatgeek/fuzzywuzzy)
	- pyicloud for interacting with the Applie iCloud service (https://github.com/picklepete/pyicloud)
	- motionless for generating static maps images out of Google Maps (https://github.com/ryancox/motionless)
	- flask-compress to provide gzip compression to flask (https://github.com/libwilliam/flask-compress)
	- jsonschema to validate the JSON configuration file (https://pypi.python.org/pypi/jsonschema)
- HTML and Javacript for the frontend, including the following libraries:
	- jQuery for event handling (https://jquery.com/)
	- Bootstrap for enhanced user experience (http://getbootstrap.com/)
	- AdminLTE as the web template (https://almsaeedstudio.com/themes/AdminLTE/index2.html)
	- Highcharts/HighStock for the charts (http://www.highcharts.com/products/highstock)
	- Font Awesome for the icons (http://fontawesome.io/icons/)
	- Bootstrap Notify for on-screen notifications (http://bootstrap-notify.remabledesigns.com/)
	- JSON Editor for the configuration editor widget (http://jeremydorn.com/json-editor/)
	- Touchspin for the input spinner component (http://www.virtuosoft.eu/code/bootstrap-touchspin/)
	- Titatoggle for the checkbox component (http://kleinejan.github.io/titatoggle/)
	- Datatables for the tables (https://datatables.net/)
	- dhtmlxScheduler for the scheduler (https://dhtmlx.com/docs/products/dhtmlxScheduler/)
- Redis for the database (http://redis.io/)

Changelog
---------------
- v1.0:
    - Weather module with static sensors
- v2.0:
    - Added new plugins and enhanced the existing
    - Re-wrote the entire logic and moved from crontab to a builtin scheduler
    - Added alerter module
    - Web interface customizable in terms of widgets and modules
    - Added logging capabilities
    - Added interactive Slack bot
    - Support for multiple data formats
    - Added configuration wizard
    - Added support for imperial measures and fahrenheit temperatures
    - Added support for actuators
    - Added installation and service scripts
    - Added automatic data expiration from the database