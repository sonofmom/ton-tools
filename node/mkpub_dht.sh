#!/bin/sh
# This script will generate JSON structure useful as TON configuration DHT record.
#
# Required params:
# DHT Node DB Directory 
# DHT Node public IP address **AS DECIMAL NOTATION!!!!**
# DHT Node port
#
# Example: mkpub_dht.sh /var/db/ton/newton-testnet-dht/db 1243007544 22222
#

GRI_BIN="generate-random-id"

DHT_NODE=$($GRI_BIN -m dht -k $1/keyring/* -a "{
            \"@type\": \"adnl.addressList\",
            \"addrs\": [
              {
                \"@type\": \"adnl.address.udp\",
                \"ip\":  $2,
                \"port\": $3
              }
            ],
            \"version\": 0,
            \"reinit_date\": 0,
            \"priority\": 0,
            \"expire_at\": 0
          }")
			  
echo $DHT_NODE | python3 -c "import sys, json; print(json.dumps(json.loads(sys.stdin.readlines()[0]), indent=2))"