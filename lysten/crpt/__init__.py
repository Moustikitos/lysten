# -*- coding:utf8 -*-

import os
import io
import lysten
import struct
import hashlib
import binascii

from six import PY3

# byte as int conversion
basint = (lambda e:e) if PY3 else \
		 (lambda e:ord(e))

# read value as binary data from buffer
unpack =  lambda fmt, fileobj: struct.unpack(fmt, fileobj.read(struct.calcsize(fmt)))

# write value as binary data into buffer
pack = lambda fmt, fileobj, value: fileobj.write(struct.pack(fmt, *value))

# read bytes from buffer
unpack_bytes = lambda f,n: unpack("<"+"%ss"%n, f)[0]

# write bytes into buffer
pack_bytes = (lambda f,v: pack("!"+"%ss"%len(v), f, (v,))) if PY3 else \
			 (lambda f,v: pack("!"+"c"*len(v), f, v))


def hexlify(data):
	result = binascii.hexlify(data)
	return result.decode() if isinstance(result, bytes) else result


def unhexlify(hexa):
	if len(hexa) % 2:
		hexa = "0" + hexa
	result = binascii.unhexlify(hexa)
	return result.encode("utf-8") if not isinstance(result, bytes) else result


def createBase(secret):
    """
    Creates a base from a given secret
    """
    hx = [e for e in "0123456789abcdef"]
    base = ""
    if not isinstance(secret, bytes):
        secret = secret.encode()
    for c in hexlify(hashlib.md5(secret).digest()):
        try:
            base += hx.pop(hx.index(c))
        except:
            pass
    return base + "".join(hx)


def scramble(base, hexa):
	"""
	Scramble given base and hex
	"""
	result = bytearray()
	for c in hexa:
		result.append(base.index(c))
	return bytes(result)


def unScramble(base, data):
	"""
	Unscramble given scrambed data using the provided base
	"""
	result = ""
	for b in data:
		result += base[basint(b)]
	return result


def dumpSignature(pin, address, privateKey, secondPrivateKey=None, name="unamed"):
	"""
	Store account data into file
	"""
	base = createBase(pin)

	folder = os.path.join(lysten.__ROOT__, ".sign", lysten.crypto.__name__.split(".")[-1])
	if not os.path.exists(folder):
		os.makedirs(folder)
	filename = os.path.join(folder, name + ".sign")
	data = bytearray()

	if isinstance(address, str):
		address = address.encode("utf-8")
	addr = scramble(base, hexlify(address))
	data.append(len(addr))
	data.extend(addr)

	key1 = scramble(base, privateKey)
	data.append(len(key1))
	data.extend(key1)

	# Checksum used to verify the data gets unscrabled correctly.
	checksum = hashlib.sha256(address).digest()
	data.append(len(checksum))
	data.extend(checksum)

	if secondPrivateKey:
		key2 = scramble(base, secondPrivateKey)
		data.append(len(key2))
		data.extend(key2)

	with io.open(filename, "wb") as out:
		out.write(data)


def loadSignature(pin, name="unamed"):
	"""
	Load account data from file
	"""
	base = createBase(pin)

	filepath = os.path.join(lysten.__ROOT__, ".sign", lysten.crypto.__name__.split(".")[-1], name + ".sign")
	result = {}
	if os.path.exists(filepath):
		with io.open(filepath, "rb") as in_:
			data = in_.read()
			try:
				data = data.encode("utf-8")
			except:
				pass

			i = 0
			len_addr = basint(data[i])
			i += 1
			result["publicKey"] = unhexlify(unScramble(base, data[i:i + len_addr]))
			i += len_addr
			len_key1 = basint(data[i])
			i += 1
			result["privateKey"] = unScramble(base, data[i:i + len_key1])
			i += len_key1
			len_checksum = basint(data[i])
			i += 1
			checksum = data[i:i + len_checksum]
			i += len_checksum

			addr_hash = hashlib.sha256(result["publicKey"]).digest()
			if addr_hash != checksum:
				raise Exception("Bad pin code")
			else:
				result["publicKey"] = result["publicKey"].decode()
				
			if i < len(data):
				len_key2 = basint(data[i])
				i += 1
				result["secondPrivateKey"] = unScramble(base, data[i:i + len_key2])

	return result


def saveSignature(pin, secret, secondSecret=None, name="unamed"):
	keys = lysten.crypto.getKeys(secret)
	if secondSecret:
		keys["secondPrivateKey"] = lysten.crypto.getKeys(secondSecret)["privateKey"]
	dumpSignature(pin, keys["publicKey"], keys["privateKey"], keys.get("secondPrivateKey", None), name)
