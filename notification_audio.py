#!/usr/bin/python
import sys
import pyaudio

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
settings = conf["output"]["audio"]
output_file = conf["constants"]["tmp_dir"]+"/audio_output.wav"
input_file = conf["constants"]["tmp_dir"]+"/audio_input.wav"

# use text to speech to notify about a given text
def notify(text):
	log.debug("Saying: "+text)
	device = "-D "+str(settings["device"]) if settings["device"] != "" else ""
	# use the picotts engine
	if settings["engine"] == "picotts": 
		# create the wav file
		log.debug(utils.run_command(["pico2wave", "-l",settings["language"],"-w",output_file, text],shell=False))
	        # play it
	        log.debug(utils.run_command("aplay "+device+" "+output_file,shell=True))
	        # remove the wav file
		utils.run_command("rm -f "+output_file)
	# use the google API
	elif settings["engine"] == "google": 
		# create the wav file
		split = settings["language"].split("-")
		language = split[0].lower() if len(split) == 2 else "en"
		log.debug(utils.run_command(["gtts-cli.py",text,"-l",language,"-o",output_file+".mp3"],shell=False))
		log.debug(utils.run_command(["mpg123","-w",output_file,output_file+".mp3"],shell=False))
		# play it
		log.debug(utils.run_command("aplay "+device+" "+output_file,shell=True))
		# remove the wav file
		utils.run_command("rm -f "+output_file+".mp3")
		utils.run_command("rm -f "+output_file)

# list all the audio devices
def show_devices():
	audio = pyaudio.PyAudio()
	info = audio.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount')
	#for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
	log.info("Probing audio devices...")
	for i in range (0,numdevices):
	        if audio.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
			# determine sample rate
			sample_rate = None
			devinfo = audio.get_device_info_by_index(i)
			for rate in [32000, 44100, 48000, 96000, 128000]:
				try: 
					audio.is_format_supported(rate,input_device=devinfo["index"],input_channels=devinfo['maxInputChannels'],input_format=pyaudio.paInt16)
					sample_rate = rate
				except: pass
                        log.info("- ["+str(i)+"][input] "+str(audio.get_device_info_by_host_api_device_index(0,i).get('name'))+", sample rate "+str(sample_rate))
	        if audio.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')>0:
        	        log.info("- ["+str(i)+"][output] "+str( audio.get_device_info_by_host_api_device_index(0,i).get('name')))

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print show_devices()
		#aa()
		print "Usage: "+__file__+" <text>"
	else:
		notify(sys.argv[1])
