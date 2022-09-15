#!/bin/bash

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# load services/pid funcs
. $CURPATH/helpers/services.sh
. $CURPATH/helpers/pid_control.sh


echo "------- Running unsafe reset all ---------"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    if command_exists $DAEMON ; then
        $DAEMON tendermint unsafe-reset-all  --home $DAEMON_HOME-$a
        echo "-- Executed $DAEMON unsafe-reset-all  --home $DAEMON_HOME-$a --"
    fi
done
