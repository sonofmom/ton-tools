#!/usr/bin/env python3
#

import sys, base64

with open(sys.argv[1], "rb+") as fd:
    print(base64.b64encode(fd.read()[4:]).decode())