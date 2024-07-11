#!/bin/bash

SRC_DS=$1
DST_DS=$2
SERVICE=$3

if ([ -z ${SRC_DS} ] || [ -z ${DST_DS} ] || [ -z ${SERVICE} ]);
then
	echo "Usage: ";
	echo "   ton_dbsync.sh <source_zfs_dataset_name> <destination_zfs_dataset_name> <service_name>";
	exit 1
fi
###
# User adjustable parameters
#

ZFS_BIN="/usr/sbin/zfs"
PV_BIN="/usr/bin/pv"
LS_BIN="/usr/bin/ls"
SYSTEMCTL_BIN="/usr/bin/systemctl"
RM_BIN="/usr/bin/rm"
FIND_BIN="/usr/bin/find"

check_errs()
{
  # Function. Parameter 1 is the return code
  # Para. 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    echo "ERROR # ${1} : ${2}"
    # as a bonus, make our script exit with the right error code.
    exit 1
  fi
}

echo "dbsync start at `date +"%d-%m-%Y %H:%M:%S"`"
echo "Performing some sanity checks"
$ZFS_BIN get all $SRC_DS@dumproot >/dev/null
check_errs $? "$SRC_DS@dumproot check failed"
$ZFS_BIN get all $DST_DS@dumproot >/dev/null
check_errs $? "$DST_DS@dumproot check failed"
$LS_BIN $DB_PATH >/dev/null 2>&1
check_errs $? "$DB_PATH does not exist"

$ZFS_BIN get all $SRC_DS@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$SRC_DS@dumpdelta found, removing"
	$ZFS_BIN destroy $SRC_DS@dumpdelta
	check_errs $? "removal failed"
fi

$ZFS_BIN get all $DST_DS@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$DST_DS@dumpdelta found, removing"
	$ZFS_BIN destroy $DST_DS@dumpdelta
	check_errs $? "removal failed"
fi

echo "Looks good"

echo -n "Terminating $SERVICE service"
$SYSTEMCTL_BIN stop $SERVICE
while $SYSTEMCTL_BIN is-active --quiet $SERVICE
do
        echo -n "."
        sleep 1
done
echo " DONE"
sleep 3

DB_PATH="$($ZFS_BIN get -H mountpoint $SRC_DS | cut -f3)"

echo "Cleansing temporary files"
$FIND_BIN $DB_PATH -name 'LOG.old*' -exec $RM_BIN {} +
$FIND_BIN $DB_PATH/files/packages -name temp.archive* -mtime +1 -exec $RM_BIN -r {} +
$FIND_BIN $DB_PATH/archive/tmp -mtime +1 -exec $RM_BIN -r {} +

echo "Creating $SRC_DS@dumpdelta snapshot"
$ZFS_BIN snapshot $SRC_DS@dumpdelta
check_errs $? "creation failed"

echo "Starting $SERVICE service"
$SYSTEMCTL_BIN start $SERVICE

echo "Sending $SRC_DS@dumpdelta snapshot to $DST_DS, this will take some time!"
$ZFS_BIN send -i $SRC_DS@dumproot $SRC_DS@dumpdelta | $PV_BIN | $ZFS_BIN recv -F $DST_DS
check_errs $? "send failed"

echo "Sending complete, removing old and creating new roots"
$ZFS_BIN destroy $SRC_DS@dumproot
check_errs $? "Removal of $SRC_DS@dumproot failed"
$ZFS_BIN rename $SRC_DS@dumpdelta $SRC_DS@dumproot
check_errs $? "Rename of $SRC_DS@dumpdelta failed"

$ZFS_BIN destroy $DST_DS@dumproot
check_errs $? "Removal of $DST_DS@dumproot failed"
$ZFS_BIN rename $DST_DS@dumpdelta $DST_DS@dumproot
check_errs $? "Rename of $DST_DS@dumpdelta failed"

echo "Mission acomplished!"
echo "dbsync end at `date +"%d-%m-%Y %H:%M:%S"`"