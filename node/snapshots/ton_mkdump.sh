#!/bin/bash

DS_NAME=$1
TARGET_PATH=$2
DUMP_TYPE=$3
NAME_SUFFIX=$4

if ([ -z ${DS_NAME} ] || [ -z ${TARGET_PATH} ] || [ -z ${DUMP_TYPE} ]);
then
        echo "Usage: ";
	echo "   ton_mkdump.sh <dataset_name> <target_path> <dump_type> [naming suffix (optional)]";
        exit 1
fi

if ([ "${DUMP_TYPE}" != "tar" ] && [ "${DUMP_TYPE}" != "zfs" ]);
then
        echo "Dump type must be either tar or zfs."
        exit 1
fi

###
# User adjustable parameters
#
POOL="spinpool"
PLZIP_PARAMS="-6 -n8"
WORK_PATH="/spinpool/work"
# In Days
ARCHIVE_LIFETIME=2

TON_ZFS_FS="$POOL/$DS_NAME"
TON_ZFS_MOUNTPOINT="/$POOL/$DS_NAME"
ARCHIVE_PREFIX="ton_dump"
ARCHIVE_FILENAME="$ARCHIVE_PREFIX$NAME_SUFFIX.`date +"%d_%m_%Y.%H-%M-%S"`.$DUMP_TYPE.lz"

TAR_BIN="/usr/bin/tar"
PV_BIN="/usr/bin/pv"
PLZIP_BIN="/usr/bin/plzip"
LS_BIN="/usr/bin/ls"
LN_BIN="/usr/bin/ln"
RM_BIN="/usr/bin/rm"
FIND_BIN="/usr/bin/find"
MV_BIN="/usr/bin/mv"
STAT_BIN="/usr/bin/stat"
ZFS_BIN="/usr/sbin/zfs"

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

echo "Performing some sanity checks"
$LS_BIN $TON_ZFS_MOUNTPOINT/db/config.json >/dev/null 2>&1
check_errs $? "$TON_ZFS_MOUNTPOINT/db/config.json does not exist, sync failed?"

$LS_BIN $TARGET_PATH >/dev/null 2>&1
check_errs $? "$TARGET_PATH does not exist"

$LS_BIN $WORK_PATH >/dev/null 2>&1
check_errs $? "$WORK_PATH does not exist"

echo "Looks good!"

echo "Removing local configuration and files"
$RM_BIN -R $TON_ZFS_MOUNTPOINT/db/config.json* $TON_ZFS_MOUNTPOINT/db/keyring $TON_ZFS_MOUNTPOINT/db/dht* $TON_ZFS_MOUNTPOINT/logs $TON_ZFS_MOUNTPOINT/keys >/dev/null 2>&1

echo "Cleansing workpath"
$RM_BIN $WORK_PATH/$ARCHIVE_PREFIX$NAME_SUFFIX* >/dev/null 2>&1

if [ "${DUMP_TYPE}" == "zfs" ]
then
	echo "Making transfer snap"
	$ZFS_BIN destroy $TON_ZFS_FS@dumpstate >/dev/null 2>&1
	$ZFS_BIN snapshot $TON_ZFS_FS@dumpstate >/dev/null 2>&1

	echo "Creating ZFS archive, this will take some time!"
	$ZFS_BIN send $TON_ZFS_FS@dumpstate | $PV_BIN | $PLZIP_BIN $PLZIP_PARAMS > $WORK_PATH/$ARCHIVE_FILENAME
else
	echo "Creating TAR archive, this will take some time!"
	cd $TON_ZFS_MOUNTPOINT/db
	$TAR_BIN -c * | $PV_BIN | $PLZIP_BIN $PLZIP_PARAMS > $WORK_PATH/$ARCHIVE_FILENAME
fi

echo "Moving archive into dumps path"
$MV_BIN $WORK_PATH/$ARCHIVE_FILENAME $TARGET_PATH

echo "Linking as latest"
$RM_BIN $TARGET_PATH/latest$NAME_SUFFIX.$DUMP_TYPE.lz
$LN_BIN -s $TARGET_PATH/$ARCHIVE_FILENAME $TARGET_PATH/latest$NAME_SUFFIX.$DUMP_TYPE.lz

echo "Updating archive size file"
$STAT_BIN -c%s $TARGET_PATH/$ARCHIVE_FILENAME > $TARGET_PATH/latest$NAME_SUFFIX.size.archive.txt

echo "Updating DB size file"
$ZFS_BIN get -p -H -o value logicalused $TON_ZFS_FS > $TARGET_PATH/latest$NAME_SUFFIX.size.disk.txt

echo "Removing old archives"
$FIND_BIN $TARGET_PATH/$ARCHIVE_PREFIX$NAME_SUFFIX* -type f -mtime +$ARCHIVE_LIFETIME -exec $RM_BIN {} \;

echo "Mission acomplished!"
