#/bin/sh

## This script restarts the systemd process of the nodes.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

echo "INFO: Number of validator nodes to be resumed: $NUM_VALS"
echo "---------- Restarting systemd service files --------"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if [ -x "$(command -v systemctl)" ]; then
        sudo -S systemctl restart $DAEMON-${a}.service
        echo "-- Resumed $DAEMON-${a}.service --"
        continue
    fi

    pid_path=$DAEMON_HOME-$a/pid
    if [ -f "$pid_path" ]; then
        log_path=$DAEMON_HOME-$a/logger.log
        echo "INFO: Starting $DAEMON-$a at $DAEMON_HOME-$a home"
        DAEMON_HOME=$DAEMON_HOME-$a DAEMON_NAME=$DAEMON DAEMON_ALLOW_DOWNLOAD_BINARIES=false \
        DAEMON_RESTART_AFTER_UPGRADE=true UNSAFE_SKIP_BACKUP=false \
        cosmovisor start --home $DAEMON_HOME-$a --log_level $LOG_LEVEL > $log_path 2>&1 &

        echo $! > $pid_path
        pid_value=$(cat $pid_path)

        echo "--- Starting node..."
        echo
        echo "Logs:"
        echo "  * tail -f $log_path"
        echo
        echo "Pid:"
        echo "  * cat $pid_path = $pid_value"
    fi
done
