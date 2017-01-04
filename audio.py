#!/usr/bin/python
import sys
from array import array
from struct import pack
from sys import byteorder
import copy
import pyaudio
import wave
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
# voice recorder variables
format = pyaudio.paInt16

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
	device = "-D "+str(output_settings["device"]) if output_settings["device"] != "" else ""
	log.debug(utils.run_command("aplay "+device+" "+filename+" &",shell=True))

# list and select an input device
def get_input_device():
	audio = pyaudio.PyAudio()
	info = audio.get_host_api_info_by_index(0)
	#for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
	log.info("Probing for audio devices...")
	device = None
	for i in range (0,info.get('deviceCount')):
		# this is an output device
                if audio.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')>0:
	                log.info("- ["+str(i)+"][output] "+str( audio.get_device_info_by_host_api_device_index(0,i).get('name')))
		# this is an input device
	        if audio.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
			# detect the supported sample rate
			sample_rate = None
			for rate in [32000, 44100, 48000, 96000, 128000]:
				devinfo = audio.get_device_info_by_index(i)
				try: 
					audio.is_format_supported(rate,input_device=i,input_channels=devinfo['maxInputChannels'],input_format=format)
					sample_rate = rate
					break
				except: 
					pass
	                log.info("- ["+str(i)+"][input] "+str(audio.get_device_info_by_host_api_device_index(0,i).get('name'))+", sample rate "+str(sample_rate)+"Hz")
			# select the input device
			if device is not None: continue
			if "device_index" not in input_settings or i == input_settings["device_index"]:
				device = {"index": i, "sample_rate": rate, "channels": devinfo['maxInputChannels'], "name": str(audio.get_device_info_by_host_api_device_index(0,i).get('name'))}
	return device

# capture voice and perform speech recognition
def listen():
	# get the input device
	device = get_input_device()
	if device is None: 
		log.warning("No input device found")
		return
	log.info("Selected input device: "+device["name"])
	# initialize the oracle
	kb = oracle.init(include_widgets=False)
	while True:
		# record a voice sample
		log.info("Listening for voice commands...")
		sample_width, data = record_voice(device)
		# save it to file
		save_to_file(device,sample_width,data)
		log.info("Captured voice sample, processing...")
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

# save data to a wav file
def save_to_file(device,sample_width,data):
	data = pack('<' + ('h' * len(data)), *data)
        wave_file = wave.open(input_file, 'wb')
        wave_file.setnchannels(device["channels"])
        wave_file.setsampwidth(sample_width)
        wave_file.setframerate(device["sample_rate"])
        wave_file.writeframes(data)
        wave_file.close()

# record the voice from the microphone and return it as an array of signed shorts
def record_voice(device):
	# open the input device
	audio = pyaudio.PyAudio()
	stream = audio.open(format=format, channels=device["channels"], rate=device["sample_rate"], input=True, output=True, frames_per_buffer=conf["constants"]["voice_recorder"]["chunk_size"])
	# initialize
	audio_started = False
	silent_chunks = 0
	data_all = array('h')
	# record the voice
	while True:
        	# little endian, signed short
		data_chunk = array('h', stream.read(conf["constants"]["voice_recorder"]["chunk_size"]))
		if byteorder == 'big': data_chunk.byteswap()
	        data_all.extend(data_chunk)
		# check if the recorded chunk was silent
        	silent = max(data_chunk) < conf["constants"]["voice_recorder"]["threshold"]
		# record the voice when not in silent
	        if audio_started:
        		if silent:
				# if there is silence count the number of silent_chunks and exit when there was too much silence at the end
	        		silent_chunks += 1
	        	        if silent_chunks > (conf["constants"]["voice_recorder"]["silent_chunks_threshold"] * device["sample_rate"] / 1024): break
		        else: 
				# there is still voice, reset the silent_chunk counter
				silent_chunks = 0
		elif not silent: 
			# there is voice for the first time, set the audio as started
			audio_started = True
	# get the sample
	sample_width = audio.get_sample_size(format)
	stream.stop_stream()
	stream.close()
	audio.terminate()
	# normalize the data
	data_all = normalize(device,data_all)
	# return the sample
	return sample_width, data_all

# normalize a voice sample
def normalize(device,data_all):
	_from = 0
	_to = len(data_all) - 1
	# normalize the sample
	for i, b in enumerate(data_all):
		if abs(b) > conf["constants"]["voice_recorder"]["threshold"]:
			_from = max(0, i - device["sample_rate"]/conf["constants"]["voice_recorder"]["trim_append_ratio"])
			break
	for i, b in enumerate(reversed(data_all)):
        	if abs(b) > conf["constants"]["voice_recorder"]["threshold"]:
			_to = min(len(data_all) - 1, len(data_all) - 1 - i + device["sample_rate"]/conf["constants"]["voice_recorder"]["trim_append_ratio"])
			break
	data_all = copy.deepcopy(data_all[_from:(_to + 1)])
	# amplify the volume
	normalize_factor = (float(conf["constants"]["voice_recorder"]["normalize_db"] * conf["constants"]["voice_recorder"]["frame_max_value"])/ max(abs(i) for i in data_all))
	r = array('h')
	for i in data_all: r.append(int(i * normalize_factor))
	return r

# main
if __name__ == '__main__':
	if len(sys.argv) == 1:
		listen()
	else:
		notify(sys.argv[1])
