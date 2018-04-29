# -*- coding:utf8 -*-

import os
import re
import sys
import time
import queue
import random
import sqlite3
import threading
# import multiprocessing

import lysten
from lysten import loadJson, dumpJson, loadAction


# def revert(tx, secret, secondSecret=None, message=""):
# 	keys = lysten.crypto.getKeys(secret)
# 	if secondSecret:
# 		keys["secondPrivateKey"] = lysten.crypto.getKeys(secondSecret)["privateKey"]

# 	payload = dict([k,v] for k,v in tx.itemss() if k not in [
# 		"requesterPublicKey",
# 		"senderId",
# 		"vendorField",
# 		"signature",
# 		"signSignature",
# 		"id"
# 	])

# 	payload["vendorField"] = message
# 	payload["amount"] = tx["amount"]-tx["fee"]
# 	payload["recipientId"] = tx["senderId"]
# 	payload["senderPublicKey"] = keys["publicKey"]
# 	lysten.crypto.sign(payload, keys["privateKey"])
# 	if secondPrivateKey:
# 		lysten.crypto.sign(payload, keys["secondPrivateKey"])
# 	lysten.crypto.mark(payload)
# 	return payload


def get(entrypoint, **kwargs):
	"""
	Generic GET call using requests lib. It returns server response as dict object.
	It randomly select one of peers registered in cfg.peers list. A custom peer can
	be used.

	Argument:
	entrypoint (str) -- entrypoint url path

	Keyword argument:
	**kwargs -- api parameters as keyword argument

	Return dict
	"""
	# API response contains several fields and wanted one can be extracted using
	# a returnKey that match the field name
	return_key = kwargs.pop('returnKey', False)
	peer = kwargs.pop('peer', False)

	params = {}
	for key, val in kwargs.items():
		params[key.replace('and_', 'AND:')] = val

	peer = peer if peer else random.choice(lysten.__NETWORK__["peers"])

	try:
		response = lysten.__SESSION__.get('{0}{1}'.format(peer, entrypoint), params=params)
		data = response.json()
	except Exception as error:
		data = {"success": False, "error": error, "peer": peer}
	else:
		if return_key:
			data = data[return_key]

			if isinstance(data, dict):
				for item in ["balance", "unconfirmedBalance", "vote"]:
					if item in data:
						data[item] = float(data[item]) / 100000000
	return data


def getUnparsedBlocks():
	"""
	Return unparsed block-height list.
	"""
	statuspath = os.path.join(lysten.__ROOT__, "core.json")
	status = loadJson(statuspath)
	height = status.get("height", -1)
	last_height = get("/api/blocks/getHeight").get("height", 0)
	if height < 0:
		markLastParsedBlock(last_height)
	elif height < last_height:
		diff = last_height - height
		return [height + i for i in range(1, diff+1, 1)]
	return  []


def markLastParsedBlock(height, nb=0):
	dumpJson({
		"height":height,
		"nbtx":nb
	}, os.path.join(lysten.__ROOT__, "core.json"))


def initializeHeight(height=None):
	heights = getUnparsedBlocks() if not height else [height]
	if len(heights):
		markLastParsedBlock(max(heights))


def getTransactionsFromBlockHeight(height):
	blocks = get("/api/blocks", height=height).get("blocks", [])
	block = blocks[0] if len(blocks) else {}
	if block.get("numberOfTransactions", 0) > 0:
		return get("/api/transactions?", blockId=block.get("id")).get("transactions", [])
	return []


def _database():
	"""
	Check if needed table exists and return database cursor.
	"""
	database = sqlite3.connect(os.path.join(lysten.__ROOT__, "lysten.db"))
	database.row_factory = sqlite3.Row

	cursor = database.cursor()
	try:
		cursor.execute("CREATE TABLE executed(timestamp INTEGER, status TEXT, amount INTEGER, txid TEXT, codename TEXT, message TEXT);")
		cursor.execute("CREATE TABLE send_trigger(senderId TEXT, regex TEXT, codename TEXT, fees REAL);")
		cursor.execute("CREATE TABLE receive_trigger(recipientId TEXT, regex TEXT, codename TEXT, fees REAL);")
		cursor.execute("CREATE UNIQUE INDEX send_idx ON send_trigger(senderId, codename);")
		cursor.execute("CREATE UNIQUE INDEX receive_idx ON receive_trigger(recipientId, codename);")
	except sqlite3.Error as error:
		pass
	return database


def storeSmartbridge(timestamp, status, amount, txid, codename, message):
	db = _database()
	db.cursor().execute(
		"INSERT OR REPLACE INTO executed(timestamp, status, amount, txid, codename, message) VALUES(?,?, ?,?,?,?);",
		(timestamp, status, amount, txid, codename, message)
	)
	db.commit()


def setSenderIdTrigger(senderId, regex, codename, fees=0.01):
	db = _database()
	db.cursor().execute(
		"INSERT OR REPLACE INTO send_trigger(senderId, regex, codename, fees) VALUES(?,?,?,?);",
		(senderId, regex, codename, fees)
	)
	db.commit()


def unsetSenderIdTrigger(senderId, codename):
	db = _database()
	db.cursor().execute(
		"DELETE FROM send_trigger WHERE senderID=? AND codename=?;",
		(senderId, codename)
	)
	db.commit()


def getSenderIdTriggers():
	return _database().cursor().execute("SELECT * FROM send_trigger;").fetchall()


def setRecipientIdTrigger(recipientId, regex, codename, fees=0.01):
	db = _database()
	db.cursor().execute(
		"INSERT OR REPLACE INTO receive_trigger(recipientId, regex, codename, fees) VALUES(?,?,?,?);",
		(recipientId, regex, codename, fees)
	)
	db.commit()


def unsetRecipientIdTrigger(recipientId, codename):
	db = _database()
	db.cursor().execute(
		"DELETE FROM receive_trigger WHERE recipientId=? AND codename=?;",
		(recipientId, codename)
	)
	db.commit()


def getRecipientIdTriggers():
	return _database().cursor().execute("SELECT * FROM receive_trigger;").fetchall()


def initialize(height, s_triggers, r_triggers, lifo):
	sys.stdout.write("> searching tx on block #%s\n" % height)
	
	def execute(codename, *args, **tx):
		try:
			func = loadAction(codename)
			if not func:
				result = False #raise Exception("codename does not exists")
			else:
				result = func(*args, **tx)
		except Exception as e:
			lifo.put(dict(
				timestamp=int(time.time()),
				status="error",
				tx=tx,
				codename=codename,
				args="%s:%s"%(e.__class__.__name__, e.args[0])
			))
		else:
			if result != False:
				lifo.put(dict(
					timestamp=int(time.time()),
					status="success",
					tx=tx,
					codename=codename,
					args="%r"%args
				))
			else:
				lifo.put(dict(
					timestamp=int(time.time()),
					status="fail",
					tx=tx,
					codename=codename,
					args="%r"%args
				))

	for tx in getTransactionsFromBlockHeight(height):
		triggers = [trig for trig in s_triggers if tx["senderId"] == trig["senderId"]] +\
			       [trig for trig in r_triggers if tx["recipientId"] == trig["recipientId"]]
		for trigger in triggers:
			match = re.match(trigger["regex"], tx["vendorField"])
			if match:
				sys.stdout.write("> match on tx #%s\n" % tx["id"])
				execute(trigger["codename"], *match.groups(), **tx)


def finalize(timestamp, status, tx, codename, args):
	storeSmartbridge(timestamp, status, tx["amount"], tx["id"], codename, args)
	return False if status != "success" else True


def consume(fifo, lock):
	lock.set()
	while lock.is_set():
		try:
			elem = fifo.get_nowait()
			initialize(*elem)
		except queue.Empty:
			lock.clear()


def main():

	LOCK = threading.Event()
	LIFO = queue.LifoQueue()
	FIFO = queue.Queue()

	# when listening to account sending smartBridge tx
	s_triggers = getSenderIdTriggers()
	# when listening to account receiving smartbridget tx
	r_triggers = getRecipientIdTriggers()

	unparsed_blocks = getUnparsedBlocks()
	for height in unparsed_blocks:
		FIFO.put([height, s_triggers, r_triggers, LIFO])

	# save the last parsed block
	if len(unparsed_blocks):
		markLastParsedBlock(max(unparsed_blocks))

	threads = []
	for i in range(lysten.__CONFIG__.get("pool", 4)):
		t = threading.Thread(target=consume, args=(FIFO, LOCK))
		threads.append(t)
		t.start()
	for thread in threads:
		thread.join()

	# manage data found in the LIFO
	LOCK.set()
	# sys.stdout.write("> finalizing...\n")
	while LOCK.is_set():
		try:
			elem = LIFO.get_nowait()
			finalize(**elem)
		except queue.Empty:
			LOCK.clear()
