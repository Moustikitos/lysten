# lysten
The lightest way to bridge something with ARK

TODO::What is bridging ?

## Set a trigger

Two different types of trigger can be registered. A trigger relies on an account
address and can be activated in two ways :

 + account receives a transaction
 + account sends a transaction

On bridge-enabled blockchain, there is a specific data named `vendorField` that
can contain a 64-length-string (256 in a near future).

```python
from lysten import core
core.setSenderIdTrigger("DKf1RUGCM3G3DxdE7V7DW7SFJ4Afmvb4YU", "^arky *(\d*)[^\d].*", "test")
```

## Parse blocks

```python
from lysten import core
core.main()
```

## Versions

### 0.1.0 : First functional release
 + core module defined
 + ark and dark network available
