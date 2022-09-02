#/bin/sh

## This script serves to store Process ID functions being used in multiple files

set -e

file_exists() {
  local file=$1
  if [ -f $file ]; then
    return 0
  else
    return 1
  fi
}

kill_process() {
  local pid_file=$1

  if file_exists $pid_file; then
    pid_value=$(cat $pid_file)

    if ps --pid $pid_value &>/dev/null; then
      kill -s 15 $pid_value
      echo "-- Stopped $pid_file by killing PID: $pid_value --"
    fi
  fi
}
