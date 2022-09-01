#/bin/sh

## This script pauses the systemd process of the nodes.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

echo "INFO: Number of validator nodes to be paused: $NUM_VALS"
echo "---------- Stopping systemd service files --------"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if [ -x "$(command -v systemctl)" ]; then
        sudo -S systemctl stop $DAEMON-${a}.service
        echo "-- Stopped $DAEMON-${a}.service --"
        continue
    fi

    pid_path=$DAEMON_HOME-$a/pid
    if [ -f "$pid_path" ]; then
        pid_value=$(cat $pid_path)
        kill -s 15 $pid_value
        echo "-- Stopped $DAEMON-${a} by killing PID: $pid_value --"
    fi
done
