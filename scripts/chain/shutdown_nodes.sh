#/bin/sh

## This script stops the systemd process of the nodes and removes their data directories.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

FILES_EXISTS="true"

# checking simd-* service files exist or not
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if [ ! -f "/lib/systemd/system/$DAEMON-${a}.service" ]; then
        FILES_EXISTS="false"
        break
    fi
done

if [ $FILES_EXISTS == "true" ]; then
    echo "INFO: Number of validator nodes to be shutdown and disabled: $NUM_VALS"
    echo "---------- Stopping systemd service files --------"
    for (( a=1; a<=$NUM_VALS; a++ ))
    do
        if [ -x "$(command -v systemctl)" ]; then
            sudo -S systemctl stop $DAEMON-${a}.service
            echo "-- Stopped $DAEMON-${a}.service -"
            sudo -S systemctl stop $DAEMON-${a}-pf.service
            echo "-- Stopped $DAEMON-${a}-pf.service --"
            continue
        fi

        pid_path=$DAEMON_HOME-$a/pid
        if [ -f "$pid_path" ]; then
            pid_value=$(cat $pid_path)
            kill -s 15 $pid_value
            echo "-- Stopped $DAEMON-${a} by killing PID: $pid_value --"
        fi
    done

    echo "------- Running unsafe reset all ---------"
    for (( a=1; a<=$NUM_VALS; a++ ))
    do
        $DAEMON tendermint unsafe-reset-all  --home $DAEMON_HOME-$a
        rm -rf $DAEMON_HOME-$a
        echo "-- Executed $DAEMON unsafe-reset-all  --home $DAEMON_HOME-$a --"
    done

    if [ -x "$(command -v systemctl)" ]; then
        echo "---------- Disabling systemd process files --------"
        for (( a=1; a<=$NUM_VALS; a++ ))
        do
            sudo -S systemctl disable $DAEMON-${a}.service
            echo "-- Executed sudo -S systemctl disable $DAEMON-${a}.service --"
            sudo -S systemctl disable $DAEMON-${a}-pf.service
            echo "-- Executed sudo -S systemctl disable $DAEMON-${a}-pf.service --"
        done
    fi
else
    echo "----No simd services running-----"
fi
