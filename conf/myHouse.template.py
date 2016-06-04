### Global configuration settings
## GENERAL
debug = 0 # enable/disable debug
website = "http://home.no-ip.com/" # URL of the web interface

## DATABASE
db_hostname = 'localhost' # database hostname
db_port = 6379 # database port
db_number = 0 # database number

## EMAIL
email_server = 'localhost' # email server hostname
email_from = 'myemail@email.com' # email from
email_to = ['myemail@email.com'] # email to

## WEATHER MODULE
weather_db_schema = 'home:weather' # db schema
weather_location_lat_lon = '41.91,12.22' # latitude,longitude
weather_wunderground_api_key = "xxxxx" # Weather Underground API key
weather_weatherchannel_api_key = "xxxxxx" # Weather Channel API key
# sensors
weather_sensors = [] # Weather sensors, format {"name":"<sensor_name>","type":"<sensor_type>","args":"<command_line_args>"}
weather_sensors.append({"name":"indoor","type":"ds18b20","args":"28-0000067b9508"})
weather_sensors.append({"name":"outdoor","type":"wunderground","args":weather_location_lat_lon})
# webcams
weather_webcams = [] # List of URLs of the webcams (max 4 entries), format {"url":"<url>"}
weather_webcams.append({"url":"http://url1/a.jpg"})
weather_webcams.append({"url":"http://url2/a.jpg"})
weather_webcams.append({"url":"http://url3/a.jpg"})
weather_webcams.append({"url":"http://url4/a.jpg"})

## CONSTANTS
hour=60*60
day=24*hour

