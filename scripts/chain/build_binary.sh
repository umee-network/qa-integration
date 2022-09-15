#!/bin/bash

# set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

export REPO=$(basename $GH_URL .git)

go env 
DAEMON_EXISTS=""
CURR_VERSION=""
echo "INFO: Checking $DAEMON is installed or not"
# which $DAEMON
# $DAEMON version
if type $DAEMON &> /dev/null; then
    DAEMON_EXISTS="true"
    CURR_VERSION='v'$($DAEMON version)
fi

if [[ -z DAEMON_EXISTS || $CURR_VERSION != $CHAIN_VERSION ]]
then
    echo "INFO: Installing $DAEMON"
    if [ ! -d $REPO ]
    then
        git clone -b $CHAIN_VERSION --single-branch $GH_URL $REPO
    fi
    cd $REPO
    echo PWD: $(pwd)
    make install

    echo "Installing price-feeder binary"
    cd ./price-feeder/
    make install
    cd $CURPATH
fi

cd $HOME
echo "Installed $DAEMON version details:"
# check version
echo "[!] $($DAEMON version)"
