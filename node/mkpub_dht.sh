#!/bin/bash
# This script will generate JSON structure useful as TON configuration DHT record.
#
# Required params:
# DHT Node DB Directory
#
# Example: mkpub_dht.sh /var/ton-dht-server/db
#

DHT_DB=$1

if ([ -z ${DHT_DB} ]);
then
        echo "Usage: ";
        echo "   mkpub_dht.sh <dht_db_path>";
        exit 1
fi

GRI_BIN="generate-random-id"
JQ_BIN="jq"
NODE_IP=`$JQ_BIN -r '.addrs[0].ip' $DHT_DB/config.json`
NODE_PORT=`$JQ_BIN -r '.addrs[0].port' $DHT_DB/config.json`

if ([ -z ${NODE_IP} ] || [ -z ${NODE_PORT} ]);
then
        echo "Could not discover node address or port, is config.json present in specified database dir? ";
        exit 1
fi

DHT_NODE=$($GRI_BIN -m dht -k $DHT_DB/keyring/* -a "{
            \"@type\": \"adnl.addressList\",
            \"addrs\": [
              {
                \"@type\": \"adnl.address.udp\",
                \"ip\":  $NODE_IP,
                \"port\": $NODE_PORT
              }
            ],
            \"version\": 0,
            \"reinit_date\": 0,
            \"priority\": 0,
            \"expire_at\": 0
          }")

if ([ -z ${DHT_NODE} ]);
then
        echo "Could not generate configuration structure, is generate-random-id in path?";
        exit 1
fi

echo $DHT_NODE | python3 -c "import sys, json; print(json.dumps(json.loads(sys.stdin.readlines()[0]), indent=2))"