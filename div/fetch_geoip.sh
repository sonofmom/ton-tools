#!/bin/bash

EDITION=$1
LICENSE_KEY=$2
TARGET_PATH=$3

if ([ -z ${EDITION} ] || [ -z ${LICENSE_KEY} ] || [ -z ${TARGET_PATH} ]);
then
        echo "Usage: ";
	echo "   fetch_geoip.sh <edition> <license_key> <target_path>";
        exit 1
fi

###
# User adjustable parameters
#
FETCH_URL="https://download.maxmind.com/app/geoip_download?edition_id=$EDITION&license_key=$LICENSE_KEY&suffix=tar.gz"
WORK_ROOT="/tmp"

CURL_BIN="/usr/bin/curl"
TAR_BIN="/usr/bin/tar"
FIND_BIN="/usr/bin/find"

MKDIR_BIN="/usr/bin/mkdir"
MV_BIN="/usr/bin/mv"
LS_BIN="/usr/bin/ls"
RM_BIN="/usr/bin/rm"

check_errs()
{
  # Function. Parameter 1 is the return code
  # Para. 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    echo "ERROR # ${1} : ${2}"
    # as a bonus, make our script exit with the right error code.
    exit ${1}
  fi
}

$LS_BIN $TARGET_PATH >/dev/null 2>&1
check_errs $? "$TARGET_PATH does not exist"

WORK_PATH="$WORK_ROOT/fetch_geoip-`date +"%d_%m_%Y.%H-%M-%S"`"
echo "Creating temporary work directory"
$MKDIR_BIN $WORK_PATH >/dev/null 2>&1
check_errs $? "Failed to create work directory $WORK_PATH"

echo "Fetching $EDITION archive"
$CURL_BIN -s -o "$WORK_PATH/download.tar.gz" $FETCH_URL
check_errs $? "Failed to fetch archive"

echo "Unpacking archive"
$TAR_BIN -zxf "$WORK_PATH/download.tar.gz" -C $WORK_PATH
check_errs $? "Failed to unpack archive"

echo "Checking presence of database in extracted data"
RS=`$FIND_BIN $WORK_PATH -type f -name "*.mmdb"`
if [ "${RS}" == "" ]; then
  check_errs 1 "Could not find mmdb file in archive"
  exit ${1}
fi

echo "Moving database into target path"
$MV_BIN $RS $TARGET_PATH
check_errs $? "Failed to move file into $TARGET_PATH"

echo "Removing temporary work directory"
$RM_BIN -R $WORK_PATH
check_errs $? "Failed to remove $WORK_PATH"

echo "Mission acomplished!"
