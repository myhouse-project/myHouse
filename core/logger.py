import logging
a="a1"

#logging.basicConfig(format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

def getLogger(name):
	logger = logging.getLogger(name)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
	#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger

#logger = getLogger(__name__)
#logger.warn("log")

getLogger("root")

def test():
	logging.warn("test1")
