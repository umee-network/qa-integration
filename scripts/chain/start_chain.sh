#/bin/bash -eux

## This script sets up a multinode network and generates multilple addresses with
## balance for testing purposes.


set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# load daemons funcs
. $CURPATH/helpers/daemons.sh

ENABLE_PRICE_FEEDER=${1:-true}

# create systemd service files
for (( a=1; a<=$NUM_VALS; a++ ))
do
    start_umeed $a
done

python3 $CURPATH/../../internal/core/status.py

if $ENABLE_PRICE_FEEDER; then
    for (( a=1; a<=$NUM_VALS; a++ ))
    do
        start_price_feeder $a
    done
fi
