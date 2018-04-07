# lysten
The lightest way to bridge something with ARK

## Setting a trigger

### `lysten.core.setSenderIdTrigger(senderId, regex, codename)`
### `lysten.core.setRecipientIdTrigger(recipientId, regex, codename)`

A trigger relies on an account address and can be activated in two ways :

 + account receives a transaction
 + account sends a transaction

On bridge-enabled blockchain, there is a specific data named `vendorField` that
can contain a 64-length-string (256 in a near future).

We can define trigger as a patterned string backed in a `vendorField` transaction
sent by a specified `senderId` (account address) or received by a `recipientId`
(account address) associated to an execution `codename`.

## Removing a trigger

### `lysten.core.unsetSenderIdTrigger(senderId, codename)`
### `lysten.core.unsetRecipientIdTrigger(recipientId, codename)`

## Parsing blocks

### `core.main()`

The `main` function parses every transaction found in blocks generated since its
last call. Because of block time parameter on DPOS BC, nothing could happen between
each block creation so `main` should be performed every block creation interval.
This use case preserves bridged node resources and allows a forever execution even
if a check ends up with an error.

## Action

### `lysten.loadAction(codename)`


## Exemple

```python
>>> from lysten import core
>>> core.setSenderIdTrigger("DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU", "^arky *(\d*)[^\d].*", "test")
>>> # DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU send transaction where vendorField='arky 123 test de lysten'
>>> core.main()
> starting block parsing...
> height 3053604
> send match on tx #96779951f0aff892d2cd50993ca13986f943bf3ec7206736206bb897b163e3b6
> applying test with ('123',)...
('123',) {'recipientId': 'DTywx2qNfefZZ2Z2bjbugQgUML7yhYEatX', 'id': '96779951f0aff892d2cd50993ca13986f943bf3ec7206736206bb897b163e3b6', 'blockid': '7367081023413534202', 'senderPublicKey': '02dcb94d73fb54e775f734762d26975d57f18980314f3b67bc52beb393893bc706', 'asset': {}, 'confirmations': 190, 'amount': 100000000, 'senderId': 'DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU', 'fee': 10000000, 'timestamp': 32996070, 'vendorField': 'arky 123 test de lysten', 'signature': '30440220615bf2309a78f520ef21102407007ae7b4cf5135bef4e97a41abad014c8040de022055e7e8215a855a6b5a570aa564566373b84684b127ef61cc981af53e683fcb61', 'type': 0}
> finalizing...
> finished
```

## Versions

### 0.1.0 : First functional release
 + core module defined
 + ark and dark network available
