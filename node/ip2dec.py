#!/usr/bin/env python3
#

import sys, socket, struct

ip = sys.argv[1]
print(struct.unpack('>i',socket.inet_aton(ip))[0])

#socket.inet_ntoa(struct.pack('>i',-1062718696))

