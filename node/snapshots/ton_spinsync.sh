#!/bin/bash

DB_PATH=$1
DS_NAME=$2
SERVICE=$3

if ([ -z ${DB_PATH} ] || [ -z ${DS_NAME} ] || [ -z ${SERVICE} ]); 
then
	echo "Usage: "; 
	echo "   ton_spinsync.sh <db_path> <zfs_dataset_name> <service>"; 
	exit 1
fi
###
# User adjustable parameters
#
SRC_POOL="nvmepool"
DST_POOL="spinpool"

TON_SRC_FS="$SRC_POOL/$DS_NAME"
TON_DST_FS="$DST_POOL/$DS_NAME"
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

echo "Performing some sanity checks"
$ZFS_BIN get all $TON_SRC_FS@dumproot >/dev/null
check_errs $? "$TON_SRC_FS@dumproot check failed"
$ZFS_BIN get all $TON_DST_FS@dumproot >/dev/null
check_errs $? "$TON_DST_FS@dumproot check failed"
$LS_BIN $DB_PATH >/dev/null 2>&1
check_errs $? "$DB_PATH does not exist"

$ZFS_BIN get all $TON_SRC_FS@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$TON_SRC_FS@dumpdelta found, removing"
	$ZFS_BIN destroy $TON_SRC_FS@dumpdelta
	check_errs $? "removal failed"
fi

$ZFS_BIN get all $TON_DST_FS@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$TON_DST_FS@dumpdelta found, removing"
	$ZFS_BIN destroy $TON_DST_FS@dumpdelta
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

echo "Removing temporary files"
$FIND_BIN $DB_PATH -name 'LOG.old*' -exec $RM_BIN {} +
$RM_BIN -r $DB_PATH/files/packages/temp.archive.*

echo "Creating $TON_SRC_FS@dumpdelta snapshot"
$ZFS_BIN snapshot $TON_SRC_FS@dumpdelta
check_errs $? "creation failed"

echo "Starting $SERVICE service"
$SYSTEMCTL_BIN start $SERVICE

echo "Sending $TON_SRC_FS@dumpdelta snapshot to $TON_DST_FS, this will take some time!"
$ZFS_BIN send -i $TON_SRC_FS@dumproot $TON_SRC_FS@dumpdelta | $PV_BIN | $ZFS_BIN recv -F $TON_DST_FS
check_errs $? "send failed"

echo "Sending complete, removing old and creating new roots"
$ZFS_BIN destroy $TON_SRC_FS@dumproot
check_errs $? "Removal of $TON_SRC_FS@dumproot failed"
$ZFS_BIN rename $TON_SRC_FS@dumpdelta $TON_SRC_FS@dumproot
check_errs $? "Rename of $TON_SRC_FS@dumpdelta failed"

$ZFS_BIN destroy $TON_DST_FS@dumproot
check_errs $? "Removal of $TON_DST_FS@dumproot failed"
$ZFS_BIN rename $TON_DST_FS@dumpdelta $TON_DST_FS@dumproot
check_errs $? "Rename of $TON_DST_FS@dumpdelta failed"

echo "Mission acomplished!"
