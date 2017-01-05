#!/usr/bin/python
import sys
import copy
import speech_recognition

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()
import oracle

# variables
output_settings = conf["output"]["audio"]
input_settings = conf["input"]["audio"]
output_file = conf["constants"]["tmp_dir"]+"/audio_output.wav"
input_file = conf["constants"]["tmp_dir"]+"/audio_input.wav"

# use text to speech to notify about a given text
def notify(text):
	log.debug("Saying: "+text)
	# use the picotts engine
	if output_settings["engine"] == "picotts": 
		# create the wav file
		log.debug(utils.run_command(["pico2wave", "-l",output_settings["language"],"-w",output_file, text],shell=False))
	        # play it
		play(output_file)
	        # remove the wav file
		utils.run_command("rm -f "+output_file)
	# use the google API
	elif output_settings["engine"] == "google": 
		# create the wav file
		language = output_settings["language"]
		log.debug(utils.run_command(["gtts-cli.py",text,"-l",language,"-o",output_file+".mp3"],shell=False))
		log.debug(utils.run_command(["mpg123","-w",output_file,output_file+".mp3"],shell=False))
		# play it
		play(output_file)
		# remove the wav file
		utils.run_command("rm -f "+output_file+".mp3")
		utils.run_command("rm -f "+output_file)

# play an audio file
def play(filename):
	device = "-t alsa "+str(output_settings["device"]) if output_settings["device"] != "" else ""
	log.debug(utils.run_command("sox "+filename+" "+device+" &"))

# capture voice and perform speech recognition
def listen():
	# initialize the oracle
	kb = oracle.init(include_widgets=False)
	listening_message = True
	while True:
		if listening_message: log.info("Listening for voice commands...")
		# run sox to record a voice sample trimming silence at the beginning and at the end
	        device = "-t alsa "+str(input_settings["device"]) if input_settings["device"] != "" else ""
        	command = "sox "+device+" "+input_file+" trim 0 "+str(input_settings["recorder"]["max_duration"])+" silence 1 "+str(input_settings["recorder"]["start_duration"])+" "+str(input_settings["recorder"]["start_threshold"])+"% 1 "+str(input_settings["recorder"]["end_duration"])+" "+str(input_settings["recorder"]["end_threshold"])+"%"
	        utils.run_command(command)
		# ensure the sample contains any sound
		max_amplitude = utils.run_command("sox "+input_file+" -n stat 2>&1|grep 'Maximum amplitude'|awk '{print $3}'")
		if not utils.is_number(max_amplitude) or float(max_amplitude) == 0: 
			listening_message = False
			continue
		log.info("Captured voice sample, processing...")
		listening_message = True
		# recognize the speech
		request = ""
		if input_settings["engine"] == "google":
			# use the speech recognition engine to make google recognizing the file
			recognizer = speech_recognition.Recognizer()
			# open the input file
			with speech_recognition.AudioFile(input_file) as source:
				audio = recognizer.record(source)
			try:
				# perform the speech recognition
				results = recognizer.recognize_google(audio,show_all=True,language=input_settings["language"])
				# identify the best result
				if len(results) != 0:
					best_result = max(results["alternative"], key=lambda alternative: alternative["confidence"])
					request = best_result["transcript"]
			except speech_recognition.UnknownValueError:
				log.warning("Google Speech Recognition could not understand the audio")
			except speech_recognition.RequestError as e:
				log.warning("Could not request results from Google Speech Recognition service; {0}".format(e))
		elif input_settings["engine"] == "pocketsphinx":
			# run pocketsphinx to recognize the speech in the audio file
			language = input_settings["language"].replace("-","_")
			command = "pocketsphinx_continuous -infile "+input_file+" -hmm /usr/share/pocketsphinx/model/hmm/"+language+"/hub4wsj_sc_8k/ -dict /usr/share/pocketsphinx/model/lm/"+language+"/cmu07a.dic 2>/dev/null"
			output = utils.run_command(command)
			request = output.replace("000000000: ","")
		if input_settings["echo_request"]:
			# repeat the question
			notify("You have said:")
			play(input_file)
			notify("I have understood: "+request)
			notify("So I'd respond with:")
		# ask the oracle what to do
		response = oracle.ask(request,custom_kb=kb)
		if response["type"] == "text":
			notify(response["content"])

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		listen()
	else:
		notify(sys.argv[1])
