import subprocess
import time
import re
import Libraries.tools.general as gt

class ValidatorConsole:
    def __init__(self, args, config, log, server_address=None, client_key=None, server_key=None):
        self.log = log
        self.config = config
        self.server_address = None
        self.client_key = None
        self.server_key = None
        if server_address:
            self.server_address = server_address
        elif hasattr(args, 'server_address') and args.server_address:
            self.server_address = args.server_address
        elif 'server_address' in config and config['server_address']:
            self.server_address = '{}:{}'.format(config['server_address'], config['server_port'])
        else:
            msg = "Server address is missing"
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

        if client_key:
            self.client_key = client_key
        elif hasattr(args, 'client_key') and args.client_key:
            self.client_key = args.client_key
        elif 'client_key' in config and config['client_key']:
            self.client_key = config['client_key']
        else:
            msg = "Client key is missing"
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

        if not gt.check_file_exists(self.client_key):
            msg = "Client key {} does not exist".format(self.client_key)
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

        if server_key:
            self.server_key = server_key
        elif hasattr(args, 'server_key') and args.server_key:
            self.server_key = args.server_key
        elif 'server_key' in config and config['server_key']:
            self.server_key = config['server_key']
        else:
            msg = "Server key is missing"
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

        if not gt.check_file_exists(self.server_key):
            msg = "Server key {} does not exist".format(self.server_key)
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

        self.log.log(self.__class__.__name__, 3, 'Console binary : {}'.format(self.config["bin"]))
        self.log.log(self.__class__.__name__, 3, 'Server address : {}'.format(str(self.server_address)))
        self.log.log(self.__class__.__name__, 3, 'Client key     : {}'.format(str(self.client_key)))
        self.log.log(self.__class__.__name__, 3, 'Server key     : {}'.format(str(self.server_key)))

    def exec(self, cmd, nothrow=False, wait=None, index=None):
        self.log.log(self.__class__.__name__, 3, 'Executing command : {}'.format(cmd))
        args = [self.config["bin"],
                "--address", self.server_address,
                "--key", self.client_key,
                "--pub", self.server_key,
                "--verbosity", "0",
                "--cmd", cmd]

        if nothrow:
            process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=self.config["timeout"])
            return process.stdout.decode("utf-8")

        success = False
        output = None
        for loop in range(0, self.config["retries"]+1):
            self.log.log(self.__class__.__name__, 3, 'validatorConsole query attempt {}'.format(loop))
            try:
                start = time.time()
                process = subprocess.run(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=self.config["timeout"])
                self.log.log(self.__class__.__name__, 3, 'query runtime: {} seconds'.format(time.time() - start))
                if wait:
                    self.log.log(self.__class__.__name__, 3, 'sleeping for {} seconds'.format(wait))
                    time.sleep(wait)

                output = process.stdout.decode("utf-8")

                if process.returncode == 0:
                    success = True
                    break
                else:
                    continue

            except subprocess.TimeoutExpired:
                self.log.log(self.__class__.__name__, 3, 'validatorConsole query {}sec timeout expired'.format(self.config["timeout"]))
                continue

        if success:
            self.log.log(self.__class__.__name__, 3, 'Command successful!')
            return output
        else:
            msg = "ValidatorConsole failure after {} retries".format(loop)
            self.log.log(self.__class__.__name__, 1, msg)
            raise Exception(msg)

    def getSyncStatus(self):
        self.log.log(self.__class__.__name__, 3, 'Retrieving sync info')

        try:
            output = self.exec('getstats')
        except Exception as e:
            self.log.log(self.__class__.__name__, 1, "Could not execute `getstats`: {}".format(str(e)))
            return None

        server_time = None
        mc_block_time = None
        match = re.match(r'.+unixtime\s*(\d+).*', output, re.DOTALL)
        if match:
            server_time = match.group(1)

        match = re.match(r'.+masterchainblocktime\s*(\d+).*', output, re.DOTALL)
        if match:
            mc_block_time = match.group(1)

        if server_time and mc_block_time:
            return int(server_time) - int(mc_block_time)
        else:
            return None

    def parse_block_info(self, as_string):
        match = re.match(r'\((-?\d*),(\d*),(\d*)\)|(\w*):(\w*).+', as_string, re.M | re.I)
        if match:
            return {
                "as_string": match.group(),
                "chain": match.group(1),
                "shard": match.group(2),
                "seqno": match.group(3),
                "roothash": match.group(4),
                "filehash": match.group(5)
            }
        else:
            return None

    # end define
# end class
