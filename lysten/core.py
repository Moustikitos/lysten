# -*- coding:utf-8 -*-
# (c) Toons 2018

# from lysten import __ROOT__, __FROZEN__, __CONFIG__, __NETWORK__, __DATABASE__


# def get(entrypoint, **kwargs):
#     """
#     Generic GET call using requests lib. It returns server response as dict object.
#     It randomly select one of peers registered in cfg.peers list. A custom peer can
#     be used.

#     Argument:
#     entrypoint (str) -- entrypoint url path

#     Keyword argument:
#     **kwargs -- api parameters as keyword argument

#     Return dict
#     """
#     # API response contains several fields and wanted one can be extracted using
#     # a returnKey that match the field name
#     return_key = kwargs.pop('returnKey', False)
#     peer = kwargs.pop('peer', False)

#     params = {}
#     for key, val in kwargs.items():
#         params[key.replace('and_', 'AND:')] = val

#     peer = peer if peer else random.choice(__NETWORK__["peers"])

#     try:
#         response = requests.get(
#             '{0}{1}'.format(peer, entrypoint),
#             params=params,
#             headers=cfg.headers,
#             verify=cfg.verify,
#             timeout=cfg.timeout
#         )
#         data = response.json()
#     except Exception as error:
#         data = {"success": False, "error": error, "peer": peer}
#     else:
#         # if not data.get("success"):
#         #     return data
#         if return_key:
#             data = data[return_key]

#             if isinstance(data, dict):
#                 for item in ["balance", "unconfirmedBalance", "vote"]:
#                     if item in data:
#                         data[item] = float(data[item]) / 100000000
#     return data


def getUnparsedBlocks():
	pass


def getTransactionsFromeBlock(block_id):
	pass

