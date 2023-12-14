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
    description = 'Fetches node sync status via validator console'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     description = description)

    parser.add_argument('-l', '--life',
                        required=False,
                        dest='life',
                        action='store_true',
                        help='If specified tool will keep querying the sync and output result until stopped - OPTIONAL')

    parser.add_argument('-i', '--interval',
                        required=False,
                        type=int,
                        dest='interval',
                        default=10,
                        action='store',
                        help='Interval for queries in life mode in seconds - OPTIONAL, defaults to 10')

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

    args = parser.parse_args()
    log = Logger(verbosity=args.verbosity)
    env = ev.get_console_environment(args.instance_name, log)
    if not env['bin']:
        env['bin'] = 'validator-engine-console'

    console = ValidatorConsole(args, env, log)

    if not args.life:
        print(console.getSyncStatus())
    else:
        while True:
            start_time = int(time.time())
            try:
                rs = console.getSyncStatus()
            except Exception as e:
                rs = 'failed'

            print('[{}] {}: {}'.format(args.instance_name, gt.get_datetime_string(timestamp=int(time.time())), rs))
            runtime = (int(time.time()) - start_time)

            if runtime < args.interval:
                time.sleep(args.interval - runtime)

if __name__ == '__main__':
    run()
