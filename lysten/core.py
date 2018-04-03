# -*- coding:utf8 -*-

# from lysten import ROOT, CONFIG, actions, loadJson, dumpJson, getNetHeight

import time
import queue
import threading

CONFIG = {}
CONFIG["pool"] = 2


def getUnparsedBlocks():
	statuspath = os.path.join(ROOT, "core.json")
	status = loadJson(statuspath)
	height = status.get("height", -1)
	last_height = getNetHeight(**CONFIG)
	if height < 0:
		dumpJson({
			"height":last_height,
			"nbtx":0
		}, statuspath)
	elif height < last_height:
		diff = last_height - height
		return [height + i for i in range(1, diff+1, 1)]
	else:
		return  []


def markParsedBlocks(height, nb=0):
	statuspath = os.path.join(ROOT, "core.json")
	dumpJson({
		"height":height,
		"nbtx":nb
	}, statuspath)


def getTransactionsFromBlock(block):
	return []


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
	for i in range(CONFIG["pool"]):
		LIFO.put(True)

	# get all available triggers
	# when listening to account sending smartBridge tx
	s_triggers = getSenderIdTriggers()
	# when listening to account receiving smartbridget tx
	r_triggers = getRecipientIdTriggers()

	# producer loop
	# in the LIFO queue, push a dict containing, the tx, the function codename to execute and give
	# its the arguments parsed from the vendorField value according to registered regex
	for block in getUnparsedBlocks():
		for tx in getTransactionsFromBlock(block):
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
	for i in range(CONFIG["pool"]):
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
