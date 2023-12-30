#!/usr/bin/env python3
#
import sys
import os
import argparse
import time
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import Libraries.tools.environment as ev
import Libraries.tools.general as gt
from Classes.Logger import Logger
from Classes.ValidatorConsole import ValidatorConsole

def run():
    description = 'Set node verbosity / log level via validator console'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     description = description)

    parser.add_argument('-n', '--instance-name',
                        required=False,
                        type=str,
                        dest='instance_name',
                        default='default',
                        action='store',
                        help='Instance name to use in environmental variables parsing - OPTIONAL')

    parser.add_argument('-a', '--addr',
                        required=False,
                        type=str,
                        dest='server_address',
                        action='store',
                        help='Node / server console address:port - OPTIONAL')

    parser.add_argument('-k', '--client-key',
                        required=False,
                        type=str,
                        dest='client_key',
                        action='store',
                        help='Client key file - OPTIONAL')

    parser.add_argument('-K', '--server-key',
                        required=False,
                        type=str,
                        dest='server_key',
                        action='store',
                        help='Server key file - OPTIONAL')

    parser.add_argument('-v', '--verbosity',
                        required=False,
                        type=int,
                        default=0,
                        dest='verbosity',
                        action='store',
                        help='Verbosity 0 - 3 - OPTIONAL, default: 0')

    parser.add_argument('log_verbosity', nargs=1, help='Log verbosity - REQUIRED')

    args = parser.parse_args()
    log = Logger(verbosity=args.verbosity)
    env = ev.get_console_environment(args.instance_name, log)
    if not env['bin']:
        env['bin'] = 'validator-engine-console'

    console = ValidatorConsole(args, env, log)

    try:
        console.exec('setverbosity {}'.format(int(args.log_verbosity[0])-1), nothrow=True)
        print('OK')
    except Exception as e:
        print('ERROR: {}'.format(e))

if __name__ == '__main__':
    run()
