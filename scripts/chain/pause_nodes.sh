#/bin/sh

## This script pauses the systemd process of the nodes.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# load services/pid funcs
. $CURPATH/helpers/services.sh
. $CURPATH/helpers/pid_control.sh

echo "INFO: Number of validator nodes to be paused: $NUM_VALS"
echo "---------- Stopping systemd service files --------"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if command_exists systemctl ; then
        stop_service $DAEMON-${a}.service
        stop_service $DAEMON-${a}-pf.service
        continue
    fi

    kill_process $DAEMON_HOME-${a}/pid.${DAEMON}
    kill_process $DAEMON_HOME-${a}/pid.pf
done
