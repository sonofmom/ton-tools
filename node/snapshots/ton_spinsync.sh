#!/bin/bash

DB_PATH=$1
POOL_NAME=$2
SERVICE=$3

if ([ -z ${DB_PATH} ] || [ -z ${POOL_NAME} ] || [ -z ${SERVICE} ]); 
then
	echo "Usage: "; 
	echo "   ton_spinsync.sh <db_path> <pool_name> <service>"; 
	exit 1
fi

TON_DATA_POOL="nvmepool/$POOL_NAME"
TON_SPIN_POOL="spinpool/$POOL_NAME"
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
$ZFS_BIN get all $TON_DATA_POOL@dumproot >/dev/null
check_errs $? "$TON_DATA_POOL@dumproot check failed"
$ZFS_BIN get all $TON_SPIN_POOL@dumproot >/dev/null
check_errs $? "$TON_SPIN_POOL@dumproot check failed"
$LS_BIN $DB_PATH >/dev/null 2>&1
check_errs $? "$DB_PATH does not exist"

$ZFS_BIN get all $TON_DATA_POOL@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$TON_DATA_POOL@dumpdelta found, removing"
	$ZFS_BIN destroy $TON_DATA_POOL@dumpdelta
	check_errs $? "removal failed"
fi

$ZFS_BIN get all $TON_SPIN_POOL@dumpdelta >/dev/null 2>&1
if [ "$?" -eq "0" ]; then
	echo "$TON_SPIN_POOL@dumpdelta found, removing"
	$ZFS_BIN destroy $TON_SPIN_POOL@dumpdelta
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

echo "Cleansing temporary files"
$FIND_BIN $DB_PATH -name 'LOG.old*' -exec $RM_BIN {} +
$RM_BIN -r $DB_PATH/files/packages/temp.archive.*

echo "Creating $TON_DATA_POOL@dumpdelta snapshot"
$ZFS_BIN snapshot $TON_DATA_POOL@dumpdelta
check_errs $? "creation failed"

echo "Starting $SERVICE service"
$SYSTEMCTL_BIN start $SERVICE

echo "Sending $TON_DATA_POOL@dumpdelta snapshot to $TON_SPIN_POOL, this will take some time!"
$ZFS_BIN send -i $TON_DATA_POOL@dumproot $TON_DATA_POOL@dumpdelta | $PV_BIN | $ZFS_BIN recv -F $TON_SPIN_POOL
check_errs $? "send failed"

echo "Sending complete, removing old and creating new roots"
$ZFS_BIN destroy $TON_DATA_POOL@dumproot
check_errs $? "Removal of $TON_DATA_POOL@dumproot failed"
$ZFS_BIN rename $TON_DATA_POOL@dumpdelta $TON_DATA_POOL@dumproot
check_errs $? "Rename of $TON_DATA_POOL@dumpdelta failed"

$ZFS_BIN destroy $TON_SPIN_POOL@dumproot
check_errs $? "Removal of $TON_SPIN_POOL@dumproot failed"
$ZFS_BIN rename $TON_SPIN_POOL@dumpdelta $TON_SPIN_POOL@dumproot
check_errs $? "Rename of $TON_SPIN_POOL@dumpdelta failed"

echo "Mission acomplished!"
