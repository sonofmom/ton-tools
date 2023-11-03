#!/usr/bin/env python3
#

import sys, base64

with open(sys.argv[2], "wb") as fd:
    fd.write(bytes.fromhex('c6b41348') + base64.b64decode(sys.argv[1]))