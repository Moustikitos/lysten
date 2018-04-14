# -*- coding:utf8 -*-
import hashlib
import binascii

from ecdsa.keys import SigningKey, VerifyingKey
from ecdsa.util import sigencode_der_canonize
from ecdsa.curves import SECP256k1

from lysten.crpt import pack, pack_bytes, hexlify, unhexlify, basint
from lysten.core import get

from six import BytesIO


def compressEcdsaPublicKey(pubkey):
	first, last = pubkey[:32], pubkey[32:]
	# check if last digit of second part is even (2%2 = 0, 3%2 = 1)
	even = not bool(basint(last[-1]) % 2)
	return (b"\x02" if even else b"\x03") + first


def getKeys(secret, seed=None):
	"""
    Generate keyring containing public key, signing and checking keys as
    attribute.

    Keyword arguments:
    secret (str or bytes) -- a human passphrase
    seed (byte) -- a sha256 sequence bytes (private key actualy)

    Return dict
    """
	seed = hashlib.sha256(secret.encode("utf8") if not isinstance(secret, bytes) else secret).digest() if not seed else seed
	signingKey = SigningKey.from_secret_exponent(int(binascii.hexlify(seed), 16), SECP256k1, hashlib.sha256)
	publicKey = signingKey.get_verifying_key().to_string()
	return {
		"publicKey": hexlify(compressEcdsaPublicKey(publicKey)),
		"privateKey": hexlify(signingKey.to_string()),
	}


def getSignature(hexa, key):
	"""
	Generate signature using private key.

	Arguments:
	hexa (str) -- data as hex string
	key (str) -- a private key as hex string

	Return hex
	"""
	signingKey = SigningKey.from_string(unhexlify(key), SECP256k1, hashlib.sha256)
	return hexlify(signingKey.sign_deterministic(unhexlify(hexa), hashlib.sha256, sigencode=sigencode_der_canonize))


def getHash(**tx):
	"""
	Hash transaction.

	Argument:
	tx (dict) -- transaction

	Return hex
	"""

	buf = BytesIO()
	# write type and timestamp
	pack("<bi", buf, (tx["type"], int(tx["timestamp"])))
	# write senderPublicKey as bytes in buffer
	if "senderPublicKey" in tx:
		pack_bytes(buf, unhexlify(tx["senderPublicKey"]))
	# if there is a requesterPublicKey
	if "requesterPublicKey" in tx:
		pack_bytes(buf, unhexlify(tx["requesterPublicKey"]))
	# if there is a recipientId
	if tx.get("recipientId", False):
		recipientId = base58.b58decode_check(tx["recipientId"])
	else:
		recipientId = b"\x00"*21
	pack_bytes(buf, recipientId)
	# if there is a vendorField
	if tx.get("vendorField", False):
		vendorField = tx["vendorField"][:64].ljust(64, "\x00")
	else:
		vendorField = "\x00"*64
	pack_bytes(buf, vendorField.encode("utf8"))
	# write amount and fee value
	pack("<QQ", buf, (int(tx["amount"]), int(tx["fee"])))
	# if there is asset data
	if tx.get("asset", False):
		asset = tx["asset"]
		typ = tx["type"]
		if typ == 1 and "signature" in asset:
			pack_bytes(buf, unhexlify(asset["signature"]["publicKey"]))
		elif typ == 2 and "delegate" in asset:
			pack_bytes(buf, asset["delegate"]["username"].encode("utf-8"))
		elif typ == 3 and "votes" in asset:
			pack_bytes(buf, "".join(asset["votes"]).encode("utf-8"))
		else:
			raise Exception("Can not manage transaction type #%d"%typ)
	# if there is a signature
	if tx.get("signature", False):
		pack_bytes(buf, unhexlify(tx["signature"]))
	# if there is a second signature
	if tx.get("signSignature", False):
		pack_bytes(buf, unhexlify(tx["signSignature"]))

	result = buf.getvalue()
	buf.close()
	return hexlify(result)


def sign(tx, key):
	tx["signSignature" if "signature" in tx else "signature"] = getSignature(getHash(**tx), key)


def mark(tx):
	tx["id"] = hexlify(hashlib.sha256(getHash(**tx)).digest())

