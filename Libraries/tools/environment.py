import json
import os
import sys

import Libraries.tools.general as gt

def get_console_environment(instance_name=None, log=None):
    result = {}
    if instance_name and instance_name != 'default':
        log.log(os.path.basename(__file__), 3, "Parsing environment variables for instance '{}'".format(instance_name.upper()))
        instance_name = "_{}".format(instance_name.upper())
    else:
        log.log(os.path.basename(__file__), 3, "Parsing default environment variables")
        instance_name = ''

    ton_node_config_var = 'TON_NODE_CONFIG{}'.format(instance_name)

    result = {
        'bin':  os.environ.get('TON_CONSOLE_BIN{}'.format(instance_name)),
        'client_key': os.environ.get('TON_CONSOLE_CLIENT_KEY{}'.format(instance_name)),
        'server_key': os.environ.get('TON_CONSOLE_SERVER_KEY{}'.format(instance_name)),
        'node_config': os.environ.get('TON_NODE_CONFIG{}'.format(instance_name)),
        'server_address': None,
        'server_port': None,
        'retries': 3,
        'timeout': 5
    }

    if result['node_config'] and gt.check_file_exists(result['node_config']):
        with open(result['node_config'], 'r') as fd:
            config = json.loads(fd.read())
            result['server_address'] = gt.dec2ip(config['addrs'][0]['ip'])
            result['server_port'] = config['control'][0]['port']

    return result




