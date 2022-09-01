#/bin/sh

## This script serves to store daemons related functions
## it goes from the perspective that we have
## $DAEMON and $DAEMON-$a vars set

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# load services/pid funcs
. $CURPATH/helpers/services.sh
. $CURPATH/helpers/pid_control.sh

start_umeed() {
  VAL_NUM=$1

  echo "VAL_NUM $VAL_NUM"
  DIFF=$(($VAL_NUM - 1))
  INC=$(($DIFF * 2))
  RPC=$((16657 + $INC))

  if command_exists systemctl ; then
    start_umeed_systemctl $VAL_NUM
  else
    start_umeed_pid $VAL_NUM
  fi
  sleep 3s

  # echo "INFO: Checking $DAEMON_HOME-${VAL_NUM} chain status"
  # echo "Executing: $DAEMON status --node tcp://localhost:${RPC}"
  # $DAEMON status --node tcp://localhost:${RPC}
}

start_umeed_systemctl() {
  a=$1

  echo "INFO: Creating $DAEMON-$a systemd service file"
  echo "[Unit]
  Description=${DAEMON} daemon
  After=network.target
  [Service]
  Environment="DAEMON_HOME=$DAEMON_HOME-$a"
  Environment="DAEMON_NAME=$DAEMON"
  Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=false"
  Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
  Environment="UNSAFE_SKIP_BACKUP=false"
  Type=simple
  User=$USER
  ExecStart=$(which cosmovisor) start --home $DAEMON_HOME-$a
  Restart=on-failure
  RestartSec=3
  LimitNOFILE=4096
  [Install]
  WantedBy=multi-user.target" | sudo tee "/lib/systemd/system/$DAEMON-${a}.service"
  echo "INFO: Starting $DAEMON-${a} service"

  daemon_reload
  start_service $DAEMON-${a}
}

start_umeed_pid() {
  a=$1

  log_path=$DAEMON_HOME-$a/logger.log
  pid_path=$DAEMON_HOME-$a/pid

  echo "INFO: Starting $DAEMON-$a at $DAEMON_HOME-$a home"
  DAEMON_HOME=$DAEMON_HOME-$a DAEMON_NAME=$DAEMON DAEMON_ALLOW_DOWNLOAD_BINARIES=false \
    DAEMON_RESTART_AFTER_UPGRADE=true UNSAFE_SKIP_BACKUP=false \
    cosmovisor start --home $DAEMON_HOME-$a --log_level $LOG_LEVEL > $log_path 2>&1 &

  echo $! > $pid_path
  pid_value=$(cat $pid_path)

  echo "--- Starting node..."
  echo
  echo "Logs:"
  echo "  * tail -f $log_path"
  echo
  echo "Pid:"
  echo "  * cat $pid_path = $pid_value"
}