## Overview
This repository contains collection of helpful tools for TON Network.

## Node related 
Those scripts are helpful for anyone who wishes to operate a TON Node. Located under `/node` path:

#### IP Conversion
* `dec2ip.py` will convert decimal IP address representation into IPV4 format. 
* `ip2dec.py` will convert decimal IPV4 IP address into decimal format.

Both scripts will properly convert to and from negative decimals to be used in node configuration.

#### Key files conversion
* `key2b64.py` will convert key file to base64 representation for later usage in config files.

#### Config generators
* `mkcontrol.sh`: Generates JSON structure for validator / node console needed for node `config.json` file
* `mklite.sh`: Generates JSON structure for lite server listener needed for node `config.json` file
* `mkpub_dht.sh`: Generates JSON structure that can be used as server definition in network configuration files, requires presence of `generate-random-id` in path. 

 
