# -*- coding:utf-8 -*-
# (c) Toons 2018

import io
import os
import sys
import imp
import json
import sqlite3
import requests


__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")
__ROOT__ = os.path.abspath(os.path.dirname(sys.executable) if __FROZEN__ else __path__[0])
__DATABASE__ = sqlite3.connect(os.path.join(__ROOT__, "lysten.db"))
__DATABASE__.row_factory = sqlite3.Row
__path__.append(os.path.join(__ROOT__, "site-actions"))

__CONFIG__ = {}
__NETWORK__ = {}
__SESSION__ = requests.Session()


def loadJson(path):
	if os.path.exists(path):
		with io.open(path) as in_:
			data = json.load(in_)
	else:
		data = {}
	return data


def dumpJson(data, path):
	with io.open(path, "w" if __PY3__ else "wb") as out:
		json.dump(data, out, indent=4)


def loadConfig():
	__CONFIG__ = loadJson(os.path.join(__ROOT__, "lysten.json"))
	return __CONFIG__


def dumpConfig():
	dumpJson(__CONFIG__, os.path.join(__ROOT__, "lysten.json"))


def loadNetwork(name):
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
