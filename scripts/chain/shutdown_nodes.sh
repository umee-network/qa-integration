#/bin/sh

## This script stops the systemd process of the nodes and removes their data directories.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# load services/pid funcs
. $CURPATH/helpers/services.sh
. $CURPATH/helpers/pid_control.sh

echo "INFO: Number of validator nodes to be shutdown and disabled: $NUM_VALS"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if command_exists systemctl ; then
        stop_service $DAEMON-${a}
        stop_service $DAEMON-${a}-pf
        continue
    fi

    kill_process $DAEMON_HOME-${a}/pid.${DAEMON}
    kill_process $DAEMON_HOME-${a}/pid.pf
done

echo "------- Running unsafe reset all ---------"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    $DAEMON tendermint unsafe-reset-all  --home $DAEMON_HOME-$a
    rm -rf $DAEMON_HOME-$a
    echo "-- Executed $DAEMON unsafe-reset-all  --home $DAEMON_HOME-$a --"
done

if command_exists systemctl ; then
    echo "---------- Disabling systemd process files --------"
    for (( a=1; a<=$NUM_VALS; a++ ))
    do
        disable_service $DAEMON-${a}
        disable_service $DAEMON-${a}-pf
    done
fi
