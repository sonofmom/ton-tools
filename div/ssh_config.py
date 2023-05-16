#!/usr/bin/env python3
#
import sys
import os
import argparse
import datetime
import subprocess
from sshconf import read_ssh_config
from pathlib import Path
#ssh-keygen -f ~/Documents/scon/test -C acme -t Ed25519

def run():
    description = 'Generates or updates ssh host config.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     description = description)

    parser.add_argument('-c', '--config',
                        required=False,
                        type=str,
                        default="~/.ssh/config",
                        dest='config',
                        action='store',
                        help='Path to ssh config file, defaults to ~/.ssh/config - OPTIONAL')

    parser.add_argument('-a', '--address',
                        required=False,
                        type=str,
                        default=None,
                        dest='address',
                        action='store',
                        help='Address of the host, will default to hostname - OPTIONAL')

    parser.add_argument('-p', '--port',
                        required=False,
                        type=str,
                        default=22,
                        dest='port',
                        action='store',
                        help='SSH Port, will default to 23 - OPTIONAL')

    parser.add_argument('-u', '--user',
                        required=False,
                        type=str,
                        default=None,
                        dest='user',
                        action='store',
                        help='Username - OPTIONAL')

    parser.add_argument('-k', '--key',
                        required=False,
                        type=str,
                        default=None,
                        dest='key',
                        action='store',
                        help='Name of the key to use, if not specified will use hostname - OPTIONAL')

    parser.add_argument('-g', '--keygen',
                        required=False,
                        dest='keygen',
                        action='store_true',
                        help='Generate key if not found')

    parser.add_argument('-t', '--keytype',
                        required=False,
                        type=str,
                        default='Ed25519',
                        dest='keytype',
                        action='store',
                        help='Key type to generate, defaults to Ed25519 - OPTIONAL')

    parser.add_argument('-P', '--keypath',
                        required=False,
                        type=str,
                        default=None,
                        dest='keypath',
                        action='store',
                        help='Path to keys defaults to path of config - OPTIONAL')

    parser.add_argument('-C', '--comment',
                        required=False,
                        type=str,
                        default=None,
                        dest='comment',
                        action='store',
                        help='Comment to prepend config entry - OPTIONAL')


    parser.add_argument('hostname', nargs=1, help='Host Name - REQUIRED')

    args = parser.parse_args()
    config_file = Path(args.config)
    config_file_fp = Path(os.path.expanduser(args.config))
    if not config_file_fp.exists():
        print("FATAL: Cannot find ssh config file '{}'".format(args.config))
        sys.exit(1)

    ssh_config = read_ssh_config(config_file_fp)

    key_path = config_file.parent
    if args.keypath:
        key_path = Path(args.keypath)

    key_path_fp = Path(os.path.expanduser(key_path))

    host_name = args.hostname[0]

    key = None
    if not args.key:
        key = host_name
    else:
        key = args.key

    if not key_path_fp.joinpath(key).exists():
        if not args.keygen:
            log("WARNING: Key file '{}' does not exist and will not be generated".format(key_path.joinpath(key)))
        else:
            


        pass


        #c.add("newsvu", Hostname="ssh-new.svu.local", Port=22, User="stud1234")
    #cf.set("acme", Hostname="ssh.svu.local", Port=1234)
    #a = cf.host('acme')

#proc_args = ['ssh-keygen']
    #process = subprocess.run(proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    #                         timeout=5)
    #a = process.stdout.decode("utf-8")


    pass
    sys.exit(0)
my_file = Path("/path/to/file")
if my_file.is_file():
    # file exists
    cfg = AppConfig(parser.parse_args())
    ti = TonIndexer(cfg.config["indexer"], cfg.log)

    start_time = datetime.datetime.now()

    result = ti.get_blocks(workchain=cfg.args.workchain,
                           shard=cfg.args.shard,
                           period=cfg.args.period,
                           end_time=cfg.args.before,
                           with_transactions=False)

    runtime = (datetime.datetime.now() - start_time)

    for key, element in enumerate(result):
        if len(result) > key+1:
            print("utime: {} seqno: {} latency: {}".format(element['gen_utime'], element['seqno'], element['gen_utime'] - result[key+1]['gen_utime']))

    sys.exit(0)

def log(message):
    print(message)

if __name__ == '__main__':
    run()
