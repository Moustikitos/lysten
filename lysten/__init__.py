# -*- coding:utf-8 -*-
# (c) Toons 2018

import io
import os
import sys
import imp
import json
import sqlite3
import requests


__VERSION__ = "0.1.0"

__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")
__ROOT__ = os.path.abspath(os.path.dirname(sys.executable) if __FROZEN__ else __path__[0])
__DATABASE__ = sqlite3.connect(os.path.join(__ROOT__, "lysten.db"))

__NETWORK__ = {}
__CONFIG__ = {"path":__path__[1:]}
__SESSION__ = requests.Session()

__DATABASE__.row_factory = sqlite3.Row
__path__.append(os.path.join(__ROOT__, "site-actions"))

def loadJson(path):
	if os.path.exists(path):
		with io.open(path) as in_:
			data = json.load(in_)
	else:
		data = {}
	return data


def appendPath(path):
	__path__.append(path)
	__CONFIG__["path"] = __path__[1:]
	dumpConfig()


def dumpJson(data, path):
	with io.open(path, "w" if __PY3__ else "wb") as out:
		json.dump(data, out, indent=4)


def loadConfig():
	global __CONFIG__
	__CONFIG__ = loadJson(os.path.join(__ROOT__, "lysten.json"))
	return __CONFIG__


def dumpConfig():
	dumpJson(__CONFIG__, os.path.join(__ROOT__, "lysten.json"))


def loadNetwork(name):
	global __NETWORK__
	__NETWORK__ = loadJson(os.path.join(__ROOT__, "%s.net" % name))
	return __NETWORK__


def connect(**network):
	__NETWORK__.update(network)
	__SESSION__.verify = os.path.join(__ROOT__, "cacert.pem") if __FROZEN__ else True
	__SESSION__.headers.update({
		"nethash": __NETWORK__.get("nethash", ""),
		"version": __NETWORK__.get("version", "0.0.0"),
		"port": "%d"%__NETWORK__.get("port", 22)
	})


def loadAction(name):
	for path in __CONFIG__["path"]:
		pathes = [os.path.join(path, mod) for mod in os.listdir(path)]
		for module in [m for m in pathes if os.path.isfile(m) and os.path.splitext(m)[-1] in [".py", ".pyw"]]:
			_name = module.replace(os.sep, ":")
			try:
				imp.load_source(_name, module)
			except Exception as e:
				pass #sys.stdout.write("%r\n"%e)
			else:
				action = getattr(sys.modules[_name], name, False)
				if action:
					return action
	return False
