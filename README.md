# lysten
The lightest way to bridge something with ARK

## Setting a trigger

**`lysten.core.setSenderIdTrigger(senderId, regex, codename)`**

**`lysten.core.setRecipientIdTrigger(recipientId, regex, codename)`**

A trigger relies on an account address and can be activated in two ways :
 + account receives a transaction
 + account sends a transaction

On bridge-enabled blockchain, there is a specific data named `vendorField` that
can contain a 64-length-string (256 in a near future). A Trigger is defined as
apatterned string backed in a `vendorField` transaction sent by a specified
`senderId` or received by a `recipientId` associated to an execution `codename`.

## Removing a trigger

**`lysten.core.unsetSenderIdTrigger(senderId, codename)`**

**`lysten.core.unsetRecipientIdTrigger(recipientId, codename)`**

## Parsing blocks

**`lysten.core.main()`**

The `main` function parses every transaction found in blocks generated since its
last call. Because of block time parameter on DPOS BC, nothing could happen between
each block creation so `main` should be performed every block creation interval.
This use case preserves bridged node resources and allows a forever execution even
if a check ends up with an error.

## Action

**`lysten.loadAction(codename)`**

This function is used in `main` to execute `codename`.

`codename` is a function name to be searched accross registered folder (default
`site-actions`). This function takes a list of arguments extracted from `vendorField`
using regular expressions (trigger `regex`).

The function prototype is :
```python
def action(*args, **kw):
    pass
```
where:
 + `args` are the arguments extracted from `vendorField`
 + `kw` is the transaction payload as `json` data

## Exemple

```python
>>> import lysten
>>> network = lysten.loadNetwork("dark")
>>> lysten.connect(network)
>>> from lysten import core
>>> core.setSenderIdTrigger("DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU", "^arky *(\d*)[^\d].*", "test")
>>> # DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU send transaction where vendorField='arky 123 test de lysten'
>>> core.main()
> starting block parsing...
> height 3053604
> send match on tx #96779951f0aff892d2cd50993ca13986f943bf3ec7206736206bb897b163e3b6
> applying test with ('123',)...
('123',) {'recipientId': 'DTywx2qNfefZZ2Z2bjbugQgUML7yhYEatX', 'id': '96779951f\
0aff892d2cd50993ca13986f943bf3ec7206736206bb897b163e3b6', 'blockid': '736708102\
3413534202', 'senderPublicKey': '02dcb94d73fb54e775f734762d26975d57f18980314f3b\
67bc52beb393893bc706', 'asset': {}, 'confirmations': 190, 'amount': 100000000, \
'senderId': 'DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU', 'fee': 10000000, 'timestamp':\
 32996070, 'vendorField': 'arky 123 test de lysten', 'signature': '30440220615b\
f2309a78f520ef21102407007ae7b4cf5135bef4e97a41abad014c8040de022055e7e8215a855a6\
b5a570aa564566373b84684b127ef61cc981af53e683fcb61', 'type': 0}
> finalizing...
> finished
```

## Using `loop.py`

**`loop.forever()`**

Launches `lysten.core.main()` every interval (default 1s) until `loop.stop()` is
called.

**`loop.restart()`**

Restarts the forever loop. My be used for memory and cpu stability.

**`loop.stop()`**

Stops the `loop.forever()` loop.

**Command line use**

```
Usage: loop.py [options] [forever/stop/restart]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -n NETWORK, --network=NETWORK
                        select blockchain network [default: dark]
  -b DELAY, --delay=DELAY
                        define the delay between each main call [default: 1]
  -i INITIAL_HEIGHT, --initial-height=INITIAL_HEIGHT
                        define the initial block height to start from
  -r, --reset-height    start from the curent block height
```

## Versions

### 0.1.0 : First functional release
 + core module defined
 + ark and dark network available
