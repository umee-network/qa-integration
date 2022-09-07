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

  if command_exists systemctl ; then
    start_umeed_systemctl $VAL_NUM
  else
    start_umeed_pid $VAL_NUM
  fi
  echo "waiting for umeed start"
  sleep 3

  DIFF=$(($VAL_NUM - 1))
  INC=$(($DIFF * 2))
  RPC=$((16657 + $INC))

  echo "INFO: Checking $DAEMON_HOME-${VAL_NUM} chain status"
  echo "Executing: $DAEMON status --node tcp://localhost:${RPC}"
  $DAEMON status --node tcp://localhost:${RPC}
}

start_price_feeder() {
  VAL_NUM=$1

  DIFF=$(($VAL_NUM - 1))
  INC=$(($DIFF * 2))
  RPC=$((16657 + $INC))

  # Setup delegated price-feeder account
  ACCT_NUM=$(($VAL_NUM + 2))
  ACCT_ADDR=$($DAEMON keys show account$ACCT_NUM -a --home $DAEMON_HOME-1 --keyring-backend test)
  $DAEMON tx oracle delegate-feed-consent validator$VAL_NUM $ACCT_ADDR --keyring-backend test --from $alidator$VAL_NUM \
    --chain-id $CHAINID --home $DAEMON_HOME-$VAL_NUM --gas 2000000 --node tcp://localhost:${RPC} -y

  if command_exists systemctl ; then
    start_price_feeder_systemctl $VAL_NUM
  else
    start_price_feeder_pid $VAL_NUM
  fi
}

start_umeed_systemctl() {
  VAL_NUM=$1

  echo "INFO: Creating $DAEMON-$VAL_NUM systemd service file"
  echo "[Unit]
  Description=${DAEMON} daemon
  After=network.target
  [Service]
  Environment="DAEMON_HOME=$DAEMON_HOME-$VAL_NUM"
  Environment="DAEMON_NAME=$DAEMON"
  Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=false"
  Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
  Environment="UNSAFE_SKIP_BACKUP=false"
  Type=simple
  User=$USER
  ExecStart=$(which cosmovisor) start --home $DAEMON_HOME-$VAL_NUM
  Restart=on-failure
  RestartSec=3
  LimitNOFILE=4096
  [Install]
  WantedBy=multi-user.target" | sudo tee "/lib/systemd/system/$DAEMON-${VAL_NUM}.service"
  echo "INFO: Starting $DAEMON-${VAL_NUM} service"

  daemon_reload
  start_service $DAEMON-${VAL_NUM}
}

start_price_feeder_systemctl() {
  VAL_NUM=$1

  PF_CONFIG="${DAEMON_HOME}-${VAL_NUM}/config/price-feeder.toml"

  # Create systemd service files
  echo "INFO: Creating price-feeder $DAEMON-$VAL_NUM-pf systemd service file"
  echo "[Unit]
  Description=${DAEMON}-price-feeder daemon
  After=network.target
  [Service]
  Environment="PRICE_FEEDER_PASS=test"
  Type=simple
  User=$USER
  ExecStart=$(which price-feeder) ${PF_CONFIG}
  Restart=on-failure
  RestartSec=3
  LimitNOFILE=4096
  [Install]
  WantedBy=multi-user.target" | sudo tee "/lib/systemd/system/$DAEMON-${VAL_NUM}-pf.service"

  echo "INFO: Starting $DAEMON-${VAL_NUM}-pf service"
  daemon_reload
  start_service $DAEMON-${VAL_NUM}-pf
}

start_price_feeder_pid() {
  VAL_NUM=$1

  log_path=$DAEMON_HOME-$VAL_NUM/logger.pf.log
  pid_path=$DAEMON_HOME-$VAL_NUM/pid.pf

  PF_CONFIG="${DAEMON_HOME}-${VAL_NUM}/config/price-feeder.toml"
  PF_DAEMON=$(which price-feeder)

  echo "INFO: Starting $DAEMON-$VAL_NUM at $DAEMON_HOME-$VAL_NUM home"

  export PRICE_FEEDER_PASS=test

  # This works around the parent process RPC env variable set by prereq.sh 
  # and due to the viper.AutomaticEnv() call in the price-feeder binary
  # All other top level price-feeder config vars could conflict as well
  unset RPC

  $PF_DAEMON ${PF_CONFIG} --log-level $LOG_LEVEL > $log_path 2>&1 &

  echo $! > $pid_path
  pid_value=$(cat $pid_path)

  echo "--- Starting price feeder..."
  echo
  echo "Logs PF:"
  echo "  * tail -f $log_path"
  echo
  echo "Pid PF:"
  echo "  * cat $pid_path = $pid_value"
}

start_umeed_pid() {
  VAL_NUM=$1

  log_path=$DAEMON_HOME-$VAL_NUM/logger.${DAEMON}.log
  pid_path=$DAEMON_HOME-$VAL_NUM/pid.${DAEMON}

  echo "INFO: Starting $DAEMON-$VAL_NUM at $DAEMON_HOME-$VAL_NUM home"
  DAEMON_HOME=$DAEMON_HOME-$VAL_NUM DAEMON_NAME=$DAEMON DAEMON_ALLOW_DOWNLOAD_BINARIES=false \
    DAEMON_RESTART_AFTER_UPGRADE=true UNSAFE_SKIP_BACKUP=false \
    cosmovisor start --home $DAEMON_HOME-$VAL_NUM --log_level $LOG_LEVEL > $log_path 2>&1 &

  echo $! > $pid_path
  pid_value=$(cat $pid_path)

  echo "--- Starting price-feeder..."
  echo
  echo "Logs:"
  echo "  * tail -f $log_path"
  echo
  echo "Pid:"
  echo "  * cat $pid_path = $pid_value"
}

price_feeder_set_config() {
  VAL_NUM=$1

  DIFF=$(($VAL_NUM - 1))
  INC=$(($DIFF * 2))
  RPC=$((16657 + $INC))
  GRPC=$((9092 + $INC))
  PF_PORT=$((7171 + $INC))
  ACCT_NUM=$(($VAL_NUM + 2))

  # Copy the price-feeder config template and replace variables
  CONFIG_DIR="${DAEMON_HOME}-${VAL_NUM}/config"
  PF_CONFIG="${CONFIG_DIR}/price-feeder.toml"
  cp $CURPATH/../configs/price-feeder.toml $CONFIG_DIR

  PRICE_FEEDER_VALIDATOR=$(eval "umeed keys show validator${VAL_NUM} --home ${DAEMON_HOME}-${VAL_NUM} --bech val --keyring-backend test --output json | jq .address")
  PRICE_FEEDER_ADDRESS="\"$(eval "umeed keys show account${ACCT_NUM} -a --home $DAEMON_HOME-1 --keyring-backend test")\""
  UMEE_VAL_KEY_DIR="${DAEMON_HOME}-1"
  UMEE_VAL_HOST="tcp://localhost:${RPC}"

  sed -i -e "s/\$PF_PORT/${PF_PORT}/g" $PF_CONFIG
  sed -i -e "s/\"\$PRICE_FEEDER_VALIDATOR\"/${PRICE_FEEDER_VALIDATOR}/g" $PF_CONFIG
  sed -i -e "s/\"\$PRICE_FEEDER_ADDRESS\"/${PRICE_FEEDER_ADDRESS}/g" $PF_CONFIG
  sed -i -e "s|\"\$UMEE_VAL_KEY_DIR\"|\"${UMEE_VAL_KEY_DIR}\"|g" $PF_CONFIG
  sed -i -e "s/\$GRPC/${GRPC}/" $PF_CONFIG
  sed -i -e "s/\$RPC/${RPC}/" $PF_CONFIG
}
