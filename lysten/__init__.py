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
__path__.append(os.path.join(__ROOT__, "site-actions"))


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
	return loadJson(os.path.join(__ROOT__, "lysten.json"))


def dumpConfig():
	dumpJson(os.path.join(__ROOT__, "lysten.json"))


def loadNetwork(name):
	return loadJson(os.path.join(__ROOT__, "%s.net" % name))


def connect(**config):
	session = requests.Session()
	session.verify = os.path.join(__ROOT__, "cacert.pem") if __FROZEN__ else True
	session.headers.update({
		"nethash": config.get("nethash", ""),
		"version": config.get("version", "0.0.0"),
		"port": "%d"%config.get("port", 22)
	})
	return session


__CONFIG__ = loadConfig()
__NETWORK__ = loadNetwork(__CONFIG__.get("network", ""))
__SESSION__ = connect(**__NETWORK__)
