#/bin/sh

## This script serves to store systemctl services functions being used in multiple files

set -e

command_exists () {
  type "$1" &> /dev/null ;
}

service_running() {
  local service=$1
  if [[ $(systemctl list-units --all -t service --full --no-legend "$service.service" | sed 's/^\s*//g' | cut -f1 -d' ') == $service.service ]]; then
    return 0
  else
    return 1
  fi
}

service_exists() {
  [ $(systemctl list-unit-files "${1}*" | wc -l) -gt 3 ]
}

disable_service() {
  local service=$1
  if service_exists $service; then
    sudo -S systemctl disable $service
    echo "-- Executed sudo -S systemctl disable $service --"
  fi
}

stop_service() {
  local service=$1
  if service_running $service; then
    sudo -S systemctl stop $service
    echo "-- Executed sudo -S systemctl stop $service --"
  fi
}

restart_service() {
  local service=$1

  sudo -S systemctl restart $service
  echo "-- Executed sudo -S systemctl restart $service --"
}

start_service() {
  local service=$1

  sudo -S systemctl start $service
  echo "-- Executed sudo -S systemctl start $service --"
}

daemon_reload() {
  sudo -S systemctl daemon-reload
}
