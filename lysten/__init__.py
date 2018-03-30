# -*- encoding:utf-8 -*-
# (c) Toons 2018

import os, sys, imp, sqlite3

__PY3__ = True if sys.version_info[0] >= 3 else False
__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")
__ROOT__ = os.path.abspath(os.path.dirname(sys.executable) if __FROZEN__ else __path__[0])
__DATABASE__ = sqlite3.connect(os.path.join(__ROOT__, "lysten.db"))
