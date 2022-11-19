#!/bin/bash

###
# User adjustable parameters
#
SCRIPT_PATH="/root/scripts"
LC_BIN="/usr/bin/lite-client"
LS_KEY="/var/ton-work/keys/liteserver.pub"
LS_ADDRESS="localhost:<changeme>"
WC_BIN="/usr/bin/wc"
GREP_BIN="/usr/bin/grep"
TR_BIN="/usr/bin/tr"
SPINSYNC_PARAMS="/var/ton-work/db ton-work validator"
MKDUMP_PARAMS="ton-work /www/dumps tar"

echo "Checking if node is working"
OUTPUT=$($LC_BIN --pub $LS_KEY --addr $LS_ADDRESS -t 5 -v 0 -c last | $GREP_BIN  "seconds" | $WC_BIN -l | $TR_BIN -d '\n')

if [ ${OUTPUT} -lt 1 ];
then
  echo "Node does not work? postponing dump"
else
  echo "Node is responding, performing dump"
  $SCRIPT_PATH/ton_spinsync.sh $SPINSYNC_PARAMS
  $SCRIPT_PATH/ton_mkdump.sh $MKDUMP_PARAMS
fi
