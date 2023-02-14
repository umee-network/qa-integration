#!/bin/bash
set -e

# Load shell variables
. ./scripts/chain/ibc/hermes-relayer/hermes/variables.sh

### Restore Keys
echo "alley afraid soup fall idea toss can goose become valve initial strong forward bright dish figure check leopard decide warfare hub unusual join cart" > ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file1.txt
$HERMES_BINARY --config ./scripts/chain/ibc/hermes-relayer/hermes/config.toml keys add --chain test-1 --mnemonic-file ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file1.txt

echo "record gift you once hip style during joke field prize dust unique length more pencil transfer quit train device arrive energy sort steak upset" > ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file2.txt
$HERMES_BINARY --config ./scripts/chain/ibc/hermes-relayer/hermes/config.toml keys add --chain test-2 --mnemonic-file ./scripts/chain/ibc/hermes-relayer/hermes/mnemonic-file2.txt
