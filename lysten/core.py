# -*- coding:utf8 -*-

from lysten import __ROOT__, __CONFIG__, __SESSION__
from lysten import loadJson, dumpJson

import os
import time
import queue
import random
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

    peer = peer if peer else random.choice(__CONFIG__["peers"])

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


def markParsedBlocks(height, nb=0):
	dumpJson({
		"height":height,
		"nbtx":nb
	}, os.path.join(__ROOT__, "core.json"))


## DOES NOT WORK !
# blockid from height :		
# http://209.250.233.136:4001/api/blocks?height=4032328
# transactions from block:
# http://209.250.233.136:4001/api/transactions?blockid=4366553906931540162
def getTransactionsFromBlockHeight(height):
	blocks = get("/api/blocks", height=height)
	block = blocks[0] if len(blocks) else {}
	if block.get("numberOfTransactions", 0) > 0:
		return get("/api/transactions?", blockid=block.get("id")).get("transactions", [])
	return []
#####


# @staticmethod
# def _cursor():
# 	"""
# 	Check if needed table exists and return database cursor.
# 	"""
# 	cursor = __DATABASE__.cursor()
# 	try:
# 		cursor.execute("CREATE TABLE actions(timestamp INTEGER, txid TEXT, vendorField TEXT, amount INTEGER, codename TEXT, args TEXT);")
# 		cursor.execute("CREATE UNIQUE INDEX actions_idx ON actions(txid);")
# 	except sqlite3.Error as error:
# 		pass
# 	return cursor

# def commit(self):
# 	if self._match:
# 		Action._cursor().execute(
# 			"INSERT OR REPLACE INTO actions(timestamp, txid, vendorField, amount, codename, args) VALUES(?,?,?,?,?,?);",
# 			(int(time.time()), self.payload["id"], self.payload["vendorField"], self.payload["amount"], self.__class__.__name__, repr(self._match))
# 		)
# 		__DATABASE__.commit()
# 		return True
# 	return False

def storeSmartbridge(timestamp, status, txid, codename, message):
	pass


def setSenderIdTriggers(senderId, regex, codename, fees=0.01):
	pass


def unsetSenderIdTriggers():
	pass


def getSenderIdTriggers():
	return []


def setRecipientIdTriggers(recipientId, regex, codename, fees=0.01):
	pass


def unsetRecipientIdTriggers():
	pass


def getRecipientIdTriggers():
	return []


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
	storeSmartbridge(timestamp, status, tx["id"], codename, args)
	if status != "success":
		return revertTx(tx)
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
			for trigger in [trig for trig in s_triggers if tx["senderId"] == trigger["senderId"]]:
				match = re.match(trigger["regex"], tx["vendorField"])
				if match:
					LIFO.put(dict(tx=tx, codename=trigger["codename"], args=match.groups()))
			# fill LIFO with smartBridge actions on tx receive
			for trigger in [trig for trig in r_triggers if tx["recipientId"] == trigger["recipientId"]]:
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

	markParsedBlocks()
