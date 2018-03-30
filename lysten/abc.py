# -*- encoding:utf-8 -*-
# (c) Toons 2018

# This mocule contains the abstract class Action

from lysten import __DATABASE__

import re
import time
import sqlite3


class Action:
	"""
	"""
	
	@staticmethod
	def _cursor():
		cursor = __DATABASE__.cursor()
		try:
			cursor.execute("CREATE TABLE actions(timestamp INTEGER, txid TEXT, vendorField TEXT, amount INTEGER, codename TEXT, args TEXT);")
			cursor.execute("CREATE UNIQUE INDEX actions_idx ON actions(txid);")
		except sqlite3.Error as error:
			pass
		return cursor

	def __init__(self, regex, **payload):
		self.regex = regex
		self.refund = payload.pop("refund", 1.0)
		self.payload = payload
		self._match = False

	def revert(self):
		payload = dict([k,v] for k,v in self.payload.items() if k not in [
			"signature", "signSignature", "id",
			"asset", 
		])
		payload["amount"] = self.refund*self.payload["amount"]
		payload["recipientId"] = self.payload.get("senderId", None)
		payload["senderId"] = self.payload.get("recipientId", None)
		return payload

	def commit(self):
		if self._match:
			Action._cursor().execute(
				"INSERT OR REPLACE INTO actions(timestamp, txid, vendorField, amount, codename, args) VALUES(?,?,?,?,?,?);",
				(int(time.time()), self.payload["id"], self.payload["vendorField"], self.payload["amount"], self.__class__.__name__, repr(self._match))
			)
			__DATABASE__.commit()
			return True
		return False

	def match(self):
		match = re.match(self.regex, self.payload["vendorField"])
		if match:
			self._match = match.groups()
			return self._match
		else:
			return ()

	def run(self):
		try: self.main(*self.match())
		except: return self.revert()
		else: return self.commit()

	def main(*args):
		"""
		"""
		pass
