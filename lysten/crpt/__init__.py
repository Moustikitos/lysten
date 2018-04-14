# -*- coding:utf8 -*-

import struct
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
