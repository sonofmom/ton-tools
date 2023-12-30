#!/bin/bash

S3_CONNECTION=$1
S3_BUCKET=$2
SNAP_PATH=${3%/}
SNAP_PREFIX=$4

if ([ -z ${S3_CONNECTION} ] || [ -z ${S3_BUCKET} ] || [ -z ${SNAP_PATH} ] || [ -z ${SNAP_PREFIX} ]);
then
        echo "Usage: ";
	echo "   ton_rclone.sh <s3_connection> <s3_bucket> <snap_path> <snap_prefix>";
        exit 1
fi

###
# Parameters
#

LS_BIN="/usr/bin/ls"
FIND_BIN="/usr/bin/find"
RM_BIN="/usr/bin/rm"
STAT_BIN="/usr/bin/stat"
XARGS_BIN="/usr/bin/xargs"
CMP_BIN="/usr/bin/cmp"
RCLONE_BIN="/usr/bin/rclone"
READLINK_BIN="/usr/bin/readlink"

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

upload_file()
{
	SRC_FILE=${1}
	DST_FILE=${2}
	start_time="$(date -u +%s)"
	echo "Uploading file $SRC_FILE as $DST_FILE"
	$RCLONE_BIN copyto $SRC_FILE $S3_CONNECTION:$S3_BUCKET/$DST_FILE --s3-no-check-bucket >/dev/null 2>&1
	check_errs $? "Upload failed!"
	end_time="$(date -u +%s)"
	elapsed="$(($end_time-$start_time))"
	echo "Total of $elapsed seconds elapsed for process"
}

echo "Performing basic sanity checks"
$LS_BIN $SNAP_PATH/$SNAP_PREFIX.lz >/dev/null 2>&1
check_errs $? "$SNAP_PATH/$SNAP_PREFIX.lz does not exist"
FILE_ARCHIVE=`$READLINK_BIN -f $SNAP_PATH/$SNAP_PREFIX.lz`

$LS_BIN $SNAP_PATH/$SNAP_PREFIX.sha256sum.txt >/dev/null 2>&1
check_errs $? "$SNAP_PATH/$SNAP_PREFIX.sha256sum.txt does not exist"
FILE_SHASUM=`$READLINK_BIN -f $SNAP_PATH/$SNAP_PREFIX.sha256sum.txt`

$LS_BIN $SNAP_PATH/$SNAP_PREFIX.size.archive.txt >/dev/null 2>&1
check_errs $? "$SNAP_PATH/$SNAP_PREFIX.size.archive.txt does not exist"
FILE_SIZE_ARCHIVE=`$READLINK_BIN -f $SNAP_PATH/$SNAP_PREFIX.size.archive.txt`

$LS_BIN $SNAP_PATH/$SNAP_PREFIX.size.disk.txt >/dev/null 2>&1
check_errs $? "$SNAP_PATH/$SNAP_PREFIX.size.disk.txt does not exist"
FILE_SIZE_DISK=`$READLINK_BIN -f $SNAP_PATH/$SNAP_PREFIX.size.disk.txt`

$RCLONE_BIN ls $S3_CONNECTION:$S3_BUCKET >/dev/null 2>&1
check_errs $? "Connection to S3 $S3_CONNECTION:$S3_BUCKET could not be established"

echo "Looks good!"

echo "Comparing sha256sum of remote archive to local archive"
REMOTE_FILE=/tmp/remote_$SNAP_PREFIX.sha256sum.txt
$RM_BIN $REMOTE_FILE >/dev/null 2>&1
$RCLONE_BIN copyto $S3_CONNECTION:$S3_BUCKET/$SNAP_PREFIX.sha256sum.txt $REMOTE_FILE --s3-no-check-bucket >/dev/null 2>&1
if [ -f $REMOTE_FILE  ]; then
	if cmp -s "$REMOTE_FILE" "$FILE_SHASUM"; then
		echo "shasum of remote file seems to be the same as local, ending process."
		exit 0
	fi
fi

upload_file $FILE_ARCHIVE $SNAP_PREFIX.lz
upload_file $FILE_SHASUM $SNAP_PREFIX.sha256sum.txt
upload_file $FILE_SIZE_ARCHIVE $SNAP_PREFIX.size.archive.txt
upload_file $FILE_SIZE_DISK $SNAP_PREFIX.size.disk.txt

echo "Mission acomplished!"