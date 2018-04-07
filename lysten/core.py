# -*- coding:utf8 -*-

from lysten import __ROOT__, __CONFIG__, __SESSION__, __DATABASE__, __NETWORK__
from lysten import loadJson, dumpJson

import os
import time
import queue
import random
import sqlite3
import threading


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

    peer = peer if peer else random.choice(__NETWORK__["peers"])

    try:
        response = __SESSION__.get('{0}{1}'.format(peer, entrypoint), params=params)
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
	statuspath = os.path.join(__ROOT__, "core.json")
	status = loadJson(statuspath)
	height = status.get("height", -1)
	last_height = get("/api/blocks/getHeight").get("height", 0)
	if height < 0:
		markParsedBlocks(last_height)
	elif height < last_height:
		diff = last_height - height
		return [height + i for i in range(1, diff+1, 1)]
	else:
		return  []


def markLastParsedBlock(height, nb=0):
	dumpJson({
		"height":height,
		"nbtx":nb
	}, os.path.join(__ROOT__, "core.json"))


def getTransactionsFromBlockHeight(height):
	blocks = get("/api/blocks", height=height).get("blocks", [])
	block = blocks[0] if len(blocks) else {}
	if block.get("numberOfTransactions", 0) > 0:
		return get("/api/transactions?", blockId=block.get("id")).get("transactions", [])
	return []


def _cursor():
	"""
	Check if needed table exists and return database cursor.
	"""
	cursor = __DATABASE__.cursor()
	try:
		cursor.execute("CREATE TABLE executed(timestamp INTEGER, status TEXT, amount INTEGER, txid TEXT, codename TEXT, message TEXT);")
		cursor.execute("CREATE TABLE send_trigger(senderId TEXT, regex TEXT, codename TEXT, fees REAL);")
		cursor.execute("CREATE TABLE receive_trigger(recipientId TEXT, regex TEXT, codename TEXT, fees REAL);")
		cursor.execute("CREATE UNIQUE INDEX send_idx ON send_trigger(senderId, codename);")
		cursor.execute("CREATE UNIQUE INDEX receive_idx ON receive_trigger(recipientId, codename);")
	except sqlite3.Error as error:
		pass
	return cursor


def storeSmartbridge(timestamp, status, amount, txid, codename, message):
	_cursor().execute(
		"INSERT OR REPLACE INTO executed(timestamp, status, amount, txid, codename, message) VALUES(?,?, ?,?,?,?);",
		(timestamp, status, amount, txid, codename, message)
	)
	__DATABASE__.commit()


def setSenderIdTrigger(senderId, regex, codename, fees=0.01):
	_cursor().execute(
		"INSERT OR REPLACE INTO send_trigger(senderId, regex, codename, fees) VALUES(?,?,?,?);",
		(senderId, regex, codename, fees)
	)
	__DATABASE__.commit()


def unsetSenderIdTrigger(senderId, codename):
	_cursor().execute(
		"DELETE FROM send_trigger WHERE senderID=? AND codename=?;",
		(senderId, codename)
	)
	__DATABASE__.commit()


def getSenderIdTriggers():
	return _cursor().execute("SELECT * FROM send_trigger;").fetchall()


def setRecipientIdTrigger(recipientId, regex, codename, fees=0.01):
	_cursor().execute(
		"INSERT OR REPLACE INTO receive_trigger(recipientId, regex, codename, fees) VALUES(?,?,?,?);",
		(recipientId, regex, codename, fees)
	)
	__DATABASE__.commit()


def unsetRecipientIdTrigger(recipientId, codename):
	_cursor().execute(
		"DELETE FROM receive_trigger WHERE recipientId=? AND codename=?;",
		(recipientId, codename)
	)
	__DATABASE__.commit()


def getRecipientIdTriggers():
	return _cursor().execute("SELECT * FROM receive_trigger;").fetchall()


def consume(lifo, fifo, lock):
	while lock.is_set():
		elem = lifo.get(True)
		# if pulled elem is a dictionary
		if isinstance(elem, dict):
			try:
				result = getattr(actions, elem["codename"])(*elem["args"], **elem["tx"])
			except Exception as e:
				fifo.put(dict(timestamp=time.time(), status="error", tx=elem["tx"], codename=elem["codename"], args="%s:%s"%(e.__class__.__name__, e.args[0])))
			else:
				if result != False:
					fifo.put(dict(timestamp=time.time(), status="success", tx=elem["tx"], codename=elem["codename"], args="%r"%elem["args"]))
				else:
					fifo.put(dict(timestamp=time.time(), status="fail", tx=elem["tx"], codename=elem["codename"], args="%r"%elem["args"]))
		# if pulled element is False, unlock the while loop
		else:
			lock.clear()


def finalize(timestamp, status, tx, codename, args):
	storeSmartbridge(timestamp, status, tx["amount"], tx["id"], codename, args)
	if status != "success":
		return True #revertTx(tx)
	else:
		return False


def main():
	# needed data
	FIFO = queue.Queue()
	LIFO = queue.LifoQueue()
	LOCK = threading.Event()

	LOCK.set()
	# put False value to stop threads
	for i in range(__CONFIG__.get("pool", 2)):
		LIFO.put(True)

	# get all available triggers
	# when listening to account sending smartBridge tx
	s_triggers = getSenderIdTriggers()
	# when listening to account receiving smartbridget tx
	r_triggers = getRecipientIdTriggers()

	# producer loop
	# in the LIFO queue, push a dict containing, the tx, the function codename to execute and give
	# its the arguments parsed from the vendorField value according to registered regex
	for height in getUnparsedBlocks():
		for tx in getTransactionsFromBlockHeight(height):
			# fill LIFO with smartBridge actions on tx send
			for trigger in [trig for trig in s_triggers if tx["senderId"] == trig["senderId"]]:
				match = re.match(trigger["regex"], tx["vendorField"])
				if match:
					LIFO.put(dict(tx=tx, codename=trigger["codename"], args=match.groups()))
			# fill LIFO with smartBridge actions on tx receive
			for trigger in [trig for trig in r_triggers if tx["recipientId"] == trig["recipientId"]]:
				match = re.match(trigger["regex"], tx["vendorField"])
				if match:
					LIFO.put(dict(tx=tx, codename=trigger["codename"], args=match.groups()))

	# launch pool of consumers
	for i in range(__CONFIG__.get("pool", 2)):
		thread = threading.Thread(target=consume, args=(LIFO, FIFO, LOCK))
		thread.start()
	# wait till last thread finishes
	thread.join()

	# manage data found in the FIFO
	LOCK.set()
	while LOCK.is_set():
		try:
			data = finalize(**FIFO.get_nowait())
			if data:
				# refund the smartbridge amount if any
				pass
		except queue.Empty:
			LOCK.clear()

	markLastParsedBlock()
