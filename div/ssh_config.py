#!/usr/bin/env python3
#
import sys
import os
import argparse
import subprocess
from sshconf import read_ssh_config
from pathlib import Path

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
                        default=None,
                        dest='port',
                        action='store',
                        help='SSH Port - OPTIONAL')

    parser.add_argument('-u', '--user',
                        required=True,
                        type=str,
                        default=None,
                        dest='user',
                        action='store',
                        help='Username - REQUIRED')

    parser.add_argument('-k', '--key',
                        required=False,
                        type=str,
                        default=None,
                        dest='key',
                        action='store',
                        help='Name of the key to use, if not specified will use $user_$hostname combination - OPTIONAL')

    parser.add_argument('-g', '--keygen',
                        required=False,
                        dest='keygen_flag',
                        action='store_true',
                        help='Generate key if not found - OPTIONAL')

    parser.add_argument('-D', '--deploy',
                        required=False,
                        dest='deploy_flag',
                        action='store_true',
                        help='Deploy new key - OPTIONAL')

    parser.add_argument('-U', '--update',
                        required=False,
                        dest='update_flag',
                        action='store_true',
                        help='Update record if it already exists - OPTIONAL')

    parser.add_argument('-d', '--deploy_key',
                        required=False,
                        type=str,
                        default=None,
                        dest='deploy_key',
                        action='store',
                        help='Deploy key to use, required if deploy is enabled - OPTIONAL')

    parser.add_argument('-t', '--keytype',
                        required=False,
                        type=str,
                        default='Ed25519',
                        dest='key_type',
                        action='store',
                        help='Key type to generate, defaults to Ed25519 - OPTIONAL')

    parser.add_argument('-P', '--keypath',
                        required=False,
                        type=str,
                        default=None,
                        dest='key_path',
                        action='store',
                        help='Path to keys, defaults to path of config - OPTIONAL')

    parser.add_argument('-C', '--comment',
                        required=False,
                        type=str,
                        default=None,
                        dest='comment',
                        action='store',
                        help='Comment / key name to store in public key, defaults to $user@$hostname - OPTIONAL')

    parser.add_argument('hostname', nargs=1, help='Host Name - REQUIRED')

    args = parser.parse_args()
    config_file = Path(args.config)
    config_file_fp = Path(os.path.expanduser(args.config))
    if not config_file_fp.exists():
        print("FATAL: Cannot find ssh config file '{}'".format(args.config))
        sys.exit(1)

    ssh_config = read_ssh_config(config_file_fp)

    config_path = config_file.parent
    if args.key_path:
        key_path = Path(args.key_path)
    else:
        key_path = config_path

    if not Path(os.path.expanduser(key_path)).exists():
        print("FATAL: Key path '{}' does not exist".format(args.key_path))
        sys.exit(1)

    if args.deploy_key:
        deploy_key = Path(os.path.expanduser(args.deploy_key))
    else:
        deploy_key = None

    if args.deploy_flag:
        if not deploy_key:
            print("FATAL: Deploy key must be specified if deploy is requested")
            sys.exit(1)
        elif not deploy_key.exists():
            print("FATAL: Specified deploy key does not exit:  '{}'".format(deploy_key))
            sys.exit(1)



    mkrecord(ssh_config=ssh_config,
             host_name=args.hostname[0],
             address=args.address,
             port=args.port,
             user=args.user,
             key_path=key_path,
             key=args.key,
             key_type=args.key_type,
             keygen_flag=args.keygen_flag,
             update_flag=args.update_flag,
             comment=args.comment)


        #c.add("newsvu", Hostname="ssh-new.svu.local", Port=22, User="stud1234")
    #cf.set("acme", Hostname="ssh.svu.local", Port=1234)
    #a = cf.host('acme')

def mk_key(key, key_path, key_type, keygen_flag, comment, user, host_name):
    pass

def mkrecord(ssh_config, address, port, user, key, keygen_flag, update_flag, key_type, key_path, comment, host_name):
    if not key:
        key = "{}_{}".format(user, host_name)

    if not comment:
        comment = "{}@{}".format(user, host_name)

    key_path_expanded = Path(os.path.expanduser(key_path))
    if key_path_expanded.joinpath(key).exists():
        log("INFO: Existing key file '{}' found".format(key_path_expanded.joinpath(key)))
    else:
        if not keygen_flag:
            log("WARNING: Key file '{}' does not exist and will not be generated".format(key_path_expanded.joinpath(key)))
        else:
            ssh_keygen("{}/{}".format(key_path_expanded.absolute(), key), comment, key_type)
            if not key_path_expanded.joinpath(key).exists():
                log("ERROR: failed to generate key file")
                sys.exit(1)

    if not ssh_config.host(host_name):
        log("INFO: Creating record for host '{}'".format(host_name))
        ssh_config.add(host_name)
    elif update_flag:
        log("INFO: Updating record for host '{}'".format(host_name))
    else:
        log("INFO: Skip update existing record for host '{}'".format(host_name))
        return

    if user:
        ssh_config.set(host_name, User=user)


        #c.add("newsvu", Hostname="ssh-new.svu.local", Port=22, User="stud1234")
    #cf.set("acme", Hostname="ssh.svu.local", Port=1234)
    #a = cf.host('acme')


    ssh_config.save()


    pass

def ssh_keygen(file, comment, key_type):
    log("INFO: Generating key file '{}'".format(file))
    proc_args = ['ssh-keygen',
                 '-f', file,
                 '-C', comment,
                 '-t', key_type]
    process = subprocess.run(proc_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=5)
    out = process.stdout.decode("utf-8")

def log(message):
    print(message)

if __name__ == '__main__':
    run()
