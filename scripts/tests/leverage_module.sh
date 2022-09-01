#/bin/sh

## This script tests the unit tests inside the leverage module

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# we can pass optional arguments when running this script
# available arguments are -s/--sender, -r/--receiver, -h/--help

python3 ./internal/modules/leverage/test.py

