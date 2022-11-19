#!/bin/bash

PROXY=$1
SITE=$2
TESTSTRING=$3
SERVICE=$4

if ([ -z ${PROXY} ] || [ -z ${SITE} ] || [ -z "${TESTSTRING}" ] || [ -z ${SERVICE} ]);
then
        echo "Usage: ";
	echo "   rldp_watchdog.sh <proxy> <site> <test string> <service>";
        exit 1
fi

###
# User adjustable parameters
#
CURL_BIN="/usr/bin/curl"
SERVICE_BIN="/usr/sbin/service"
WC_BIN="/usr/bin/wc"
GREP_BIN="/usr/bin/grep"
TR_BIN="/usr/bin/tr"
DATE_FORMAT="%d-%m-%Y %H:%M:%S"
RESPONSE_BYTE_LIMIT="10240"

OUTPUT=$($CURL_BIN --max-time 10 -s --header "Range: bytes=0-$RESPONSE_BYTE_LIMIT" -x ${PROXY} ${SITE} | $GREP_BIN "${TESTSTRING}" | $WC_BIN -l | $TR_BIN -d '\n')
NOW=$(date +"$DATE_FORMAT")

if [ ${OUTPUT} -lt 1 ];
then
  echo "$NOW: Bad, restarting service"
  $SERVICE_BIN ${SERVICE} restart
else
  echo "$NOW: OK"
fi
