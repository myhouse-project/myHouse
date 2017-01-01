#!/usr/bin/python
import sys
import cv2
import numpy
import os.path
import base64

import utils
import logger
import config
log = logger.get_logger(__name__)
conf = config.get_config()

# variables
detect_objects_debug = False

# return a cv2 image object from a binary image
def import_image(data,is_base64=False):
	if is_base64: data = base64.b64decode(data)
        image = numpy.asarray(bytearray(data), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
	return image

# return a binary image from a cv2 object
def export_image(image,is_base64=False):
	r, buffer = cv2.imencode(".png",image)
	data = buffer.tostring()
	if is_base64: data = base64.b64encode(data)
	return data

# normalize an image
def normalize(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
	return gray

# detect objects in a given image
def detect_objects(image,is_base64=False):
	# read the image
	image = import_image(image,is_base64=is_base64)
	# normalize the image
	normalized = normalize(image)
	# for each detection feature
        for feature in conf["alerter"]["object_detection"]:
		# load the cascade file
                filename = conf["constants"]["base_dir"]+"/"+feature["filename"]
                if not os.path.isfile(filename):
                        log.error("Unable to load the detection object XML at "+filename)
                        return None
                cascade = cv2.CascadeClassifier(filename)
                # perform the detection
                objects = cascade.detectMultiScale(
                        normalized,
                        scaleFactor=feature["scale_factor"],
                        minNeighbors=feature["min_neighbors"],
                        minSize=(feature["min_size"],feature["min_size"]),
                        maxSize=(feature["max_size"],feature["max_size"]),
                        flags = cv2.cv.CV_HAAR_SCALE_IMAGE
                )
                # nothing found, go to the next object
                if len(objects) == 0: continue
                # return the number of objects detected
                else:
			# found draw a rectangle around each object
			for (x, y, w, h) in objects:
                        	cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
			# prepare the alert text
			text = str(len(objects))+" "+feature["object"]
			# if debug is on save the image
			if detect_objects_debug: cv2.imwrite(conf["constants"]["tmp_dir"]+"/detect_objects_"+str(utils.now())+".png",image)
			# prepare the image
			image = export_image(image,is_base64=is_base64)
			return [text,image]
	# nothing found, return None
	return None

