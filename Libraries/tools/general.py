import os
import time
import socket
import struct

def check_path_exists(path):
    if os.path.exists(path) and os.path.isdir(path) and os.access(path, os.R_OK):
        return True
    else:
        return False


def check_path_writable(path):
    if os.path.exists(path) and os.path.isdir(path) and os.access(path, os.W_OK):
        return True
    else:
        return False


def check_file_exists(file):
    if os.path.exists(file) and os.path.isfile(file) and os.access(file, os.R_OK):
        return True
    else:
        return False


def check_file_writable(file):
    if os.path.exists(file) and os.path.isfile(file) and os.access(file, os.W_OK):
        return True
    else:
        return False


def get_datetime_string(timestamp=time.time()):
    return time.strftime("%d.%m.%Y %H:%M:%S %Z", time.localtime(timestamp))

def dec2ip(value):
    return socket.inet_ntoa(struct.pack('>i', int(value)))


def ip2dec(value):
    return struct.unpack('>i',socket.inet_aton(value))[0]

def unique(data):
    return list(set(data))
