#!/usr/bin/env python3
#
import re
import sys
import argparse
import subprocess
import base64
import socket, struct

verbosity = None
def run():
    global verbosity

    description = 'Resolve ADNL address to IP:Port combination using DHT servers'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)

    parser.add_argument('-r', '--resolver',
                        required=True,
                        type=str,
                        dest='resolver',
                        action='store',
                        help='Path to dht-resolve binary - REQUIRED')

    parser.add_argument('-c', '--config',
                        required=True,
                        type=str,
                        dest='config',
                        action='store',
                        help='TON network config - REQUIRED')

    parser.add_argument('-v', '--verbosity',
                        required=False,
                        type=int,
                        dest='verbosity',
                        action='store',
                        default=1,
                        help='Verbosity - OPTIONAL')

    parser.add_argument('adnl', nargs=1, help='ADNL address to resolve - REQUIRED')
    args = parser.parse_args()
    verbosity = args.verbosity

    log('Attempting to resolve ADNL {}'.format(args.adnl[0]))
    log('Please wait, this can take some time')
    process_args = [args.resolver,
            "--global-config", args.config,
            "--key-id", base64.b64encode(bytes.fromhex(args.adnl[0])).decode(),
            "--key-name", "address",
            "--timeout", "10"]

    ip = None
    port = None
    try:
        process = subprocess.run(process_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=10)
        out = process.stdout.decode("utf-8")

        match = re.match(r'.+\nVALUE: (.+)', out, re.MULTILINE)
        if match:
            result = base64.b64decode(match.group(1))
            ip   = socket.inet_ntoa(struct.pack('>i',int.from_bytes(result[12:16], byteorder='little', signed=True)))
            port = int.from_bytes(result[16:20], byteorder='little', signed=True)

    except subprocess.TimeoutExpired:
        log('Timeout')

    if ip:
        log('Got result:')
        print("{}:{}".format(ip,port))
    else:
        log('Could not resolve, please retry or check ADNL')


def log(message):
    global verbosity
    if verbosity:
        print(message)

if __name__ == '__main__':
    run()
