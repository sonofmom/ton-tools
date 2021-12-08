#!/usr/bin/env python3
#

import sys, codecs

f=open(sys.argv[1], "rb+")
pub=f.read()[4:]
print(codecs.decode(codecs.encode(pub,"base64"), "utf8").replace("\n",""))
