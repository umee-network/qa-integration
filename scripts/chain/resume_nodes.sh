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
    if command_exists systemctl ; then
        restart_service $DAEMON-${a}.service
        restart_service $DAEMON-${a}-pf.service
        continue
    fi

    start_umeed $a
    start_price_feeder $a
done
