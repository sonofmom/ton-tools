#!/usr/bin/env python3
#

import sys, socket, struct

ip = int(sys.argv[1])
print(socket.inet_ntoa(struct.pack('>i',ip)))
