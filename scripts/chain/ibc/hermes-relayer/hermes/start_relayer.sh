#!/bin/bash

# Load shell variables
. ./scripts/chain/ibc/hermes-relayer/hermes/variables.sh

# Start the hermes relayer in multi-paths mode
echo "Starting hermes relayer..."
$HERMES_BINARY --config $CONFIG_DIR start