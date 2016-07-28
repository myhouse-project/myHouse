#!/usr/bin/python
import sys
import os
import re

import utils
import logger
logger = logger.get_logger(__name__)

# read the measure
def read(sensor,measure):
	filename = sensor["args"][0]
	logger.debug("Reading "+filename)
        with open(filename, 'r') as content_file:
		return content_file.read()

# parse the measure
def parse(sensor,measure,data):
	regexp = sensor["args"][1]
	m = re.search(regexp,data)
	return m.group(0)

# return the cache schema
def schema(measure):
	return measure
