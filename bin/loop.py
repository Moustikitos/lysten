# -*- coding:utf-8 -*-

import io
import os
import sys
import json
import time
import random
import traceback
import threading

from lysten import loadJson, dumpJson, loadNetwork, __ROOT__
from lysten.core import main, initializeHeight

PY3 = True if sys.version_info[:2] >= (3,0) else True
CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.path.splitext(__file__)[0]+".json")


def stop():
	data = loadJson(CONFIG)
	data["stop forever"] = True
	dumpJson(data, CONFIG)


def stop_asked():
	data = loadJson(CONFIG)
	return data.get("stop forever", False)


def stop_done():
	data = loadJson(CONFIG)
	data.pop("stop forever", False)
	dumpJson(data, CONFIG)


def call(func, *args, **kwargs):
	try:
		func(*args, **kwargs)
	except Exception as e:
		sys.stderr.write("%s\n" % e)
		traceback.print_tb(e.__traceback__, file=sys.stderr)


def forever():
	data = loadJson(CONFIG)
	sys.stdout.write(">>> forever started :\n")
	while True:
		sys.stdout.flush()
		sys.stderr.flush()
		if stop_asked():
			break
		else:
			time.sleep(data.get("blocktime", 1))
			threading.Thread(target=call, args=(main,)).start()
	sys.stdout.write(">>> finishing remaining tasks...\n")
	while len(threading.enumerate()) > 1:
		time.sleep(data.get("blocktime", 1))
	sys.stdout.write(">>> forever stoped !\n")
	stop_done()


def restart():
	data = loadJson(CONFIG)
	stop()
	while stop_asked():
		time.sleep(data.get("blocktime", 1))
	forever()


if __name__ == "__main__":
	import optparse
	data = loadJson(CONFIG)

	parser = optparse.OptionParser()
	parser.add_option("-n", "--network", dest="network", type="string", default="dark")
	parser.add_option("-b", "--blocktime", dest="blocktime", type="int", default=1)
	parser.add_option("-i", "--initial-height", dest="initial_height", type="int", default=None)
	parser.add_option("-r", "--reset-height", dest="reset_height", action="store_true", default=False)
	options, args = parser.parse_args()

	loadNetwork(options.network)
	status = os.path.join(__ROOT__, "core.json")
	if options.initial_height:
		initializeHeight(options.initial_height)
	elif options.reset_height:
		if os.path.exists(status):
			os.remove(status)
		initializeHeight(None)

	data["network"] = options.network
	data["blocktime"] = options.blocktime
	dumpJson(data, CONFIG)

	if len(args) == 1:
		if args[-1] in ["init", "restart", "forever", "stop"]:
			getattr(sys.modules[__name__], args[-1])()
		else:
			sys.stdout.write("%s command does not exist\n" % args[-1])
	else:
		raise Exception("only one command can be performed")

