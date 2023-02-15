#!/bin/bash
set -e

# Load shell variables
. ./scripts/chain/ibc/hermes-relayer/hermes/variables.sh

### Restore Keys
$HERMES_BINARY --config ./scripts/chain/ibc/hermes-relayer/hermes/config.toml keys add --chain test-1 --mnemonic-file ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file1.txt

$HERMES_BINARY --config ./scripts/chain/ibc/hermes-relayer/hermes/config.toml keys add --chain test-2 --mnemonic-file ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file2.txt
