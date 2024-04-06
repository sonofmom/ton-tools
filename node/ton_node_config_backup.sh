#!/bin/bash

DB_PATH=${1%/}
BACKUP_PATH=${2%/}
KEEP_COUNT=$3

if ([ -z ${DB_PATH} ] || [ -z ${BACKUP_PATH} ] || [ -z ${KEEP_COUNT} ]);
then
        echo "Usage: ";
	echo "   ton_node_config_backup.sh <database_path> <backup_path> <backups_keep_count>";
        exit 1
fi

BACKUP_NAME="`date +"%Y-%m-%d_%H.%M.%S"`"
LS_BIN="/usr/bin/ls"
LN_BIN="/usr/bin/ln"
RM_BIN="/usr/bin/rm"
CP_BIN="/usr/bin/cp"
MKDIR_BIN="/usr/bin/mkdir"
STAT_BIN="/usr/bin/stat"
TAIL_BIN="/usr/bin/tail"
EXPR_BIN="/usr/bin/expr"
XARGS_BIN="/usr/bin/xargs"

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

echo "Checking presence of backup path"
$LS_BIN $BACKUP_PATH >/dev/null 2>&1
check_errs $? "$BACKUP_PATH does not exist"

echo "Checking if backup path is declared as such"
$LS_BIN $BACKUP_PATH/.ton_backup_path >/dev/null 2>&1
check_errs $? "File .ton_backup_path must exist in your backup path, please touch it first"

echo "Checking presence of config.json"
$LS_BIN $DB_PATH/config.json >/dev/null 2>&1
check_errs $? "$DB_PATH/config.json does not exist"

echo "Checking config.json size"
if [ `$STAT_BIN -c%s $DB_PATH/config.json` -eq "0" ]; then
    echo "Config file has 0 size, probably broken, aborting backup"
    exit 1
fi

BACKUP_DIR=$BACKUP_PATH/$BACKUP_NAME
echo "Creating backup directory"
$MKDIR_BIN $BACKUP_DIR
check_errs $? "Cannot create backup directory $BACKUP_DIR"

echo "Copying config"
$CP_BIN -rp $DB_PATH/config.json $BACKUP_DIR
check_errs $? "Copying of config failed!"

echo "Copying keyring"
$CP_BIN -rp $DB_PATH/keyring $BACKUP_DIR
check_errs $? "Copying of keyring failed!"

if [ -e "$BACKUP_PATH/latest" ]; then
    echo "Removing old latest link"
    $RM_BIN "$BACKUP_PATH/latest"
fi

echo "Removing old backups"
cd $BACKUP_PATH && $LS_BIN -tp | $TAIL_BIN -n +$($EXPR_BIN $KEEP_COUNT + 1) | $XARGS_BIN -I {} $RM_BIN -R -- {}

echo "Creating latest link"
$LN_BIN -s $BACKUP_DIR $BACKUP_PATH/latest

echo "Mission acomplished!"