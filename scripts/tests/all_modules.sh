#/bin/sh

## This script generates and broadcasts 1000 transfers to and fro between two accounts.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

cd $PWD/internal/modules
# we can pass optional arguments when running this script
# available arguments are -s/--sender, -r/--receiver, -n/--num_txs, -h/--help
# example: ./all_modules.sh -s cosmos1f2838advrjl3c8h4kjfvfmhkh0gs0wf6cyzwu8 -r osmo1cytlejwrejz8wajslgqwczlzazxaxhf4hccly5 -n 10
for f in *; do
    if [[ -d "$f" && -f "./$f/test.py" ]]; then
        # Will not run if no directories are available
        # or no test file found in module
        python3 ./$f/test.py
    fi
done
