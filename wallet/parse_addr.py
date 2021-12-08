#!/usr/bin/env python3
#
import sys
import struct
import os
import json
from pyTON import address_utils

format    = 'text'
file      = None

def init(argv):
    global format, file

    for argument in argv:
        if argument == '-j':
            format = 'json'
        elif argument[0] != '-':
            file = argument

    if not file:
        print_usage()
        sys.exit(1)

    if not os.access(file, os.R_OK):
        print("Address file " + file + " could not be opened")
        sys.exit(1)

def print_usage():
    print("Usage: parse_addr.py OPTIONS INPUT_FILE ")
    print("OPTIONS:")
    print("  -j: Output result as JSON")

def run():
    global file
    addr = {}
    addr["raw"] = open(file, "rb+").read()
    addr["wc"] = str(struct.unpack("i", addr["raw"][32:])[0])
    addr["hex"] = addr["raw"][:32].hex()
    addr["hex_full"] = addr["wc"] + ":" + addr["hex"]
    addr.update(address_utils.account_forms(addr["hex_full"]))
    addr.pop('bytes', None)
    addr.pop('raw', None)

    if format == 'json':
        print(json.dumps(addr))
    else:
        print("Workchain     : {}".format(addr["wc"]))
        print("Hexadecimal   : {}".format(addr["hex_full"]))
        print("Bounceable    : {}".format(addr["bounceable"]["b64url"]))
        print("Non bounceable: {}".format(addr["non_bounceable"]["b64url"]))

if __name__ == '__main__':
    init(sys.argv[1:])
    run()
