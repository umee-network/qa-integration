#!/bin/bash


set -e

CWD="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

BINARY="$1"
CHAIN_DIR=./data
CHAINID_1=test-1
CHAINID_2=test-2

VAL_MNEMONIC_1="copper push brief egg scan entry inform record adjust fossil boss egg comic alien upon aspect dry avoid interest fury window hint race symptom"
VAL_MNEMONIC_2="maximum display century economy unlock van census kite error heart snow filter midnight usage egg venture cash kick motor survey drastic edge muffin visual"
WALLET_MNEMONIC_1="banner spread envelope side kite person disagree path silver will brother under couch edit food venture squirrel civil budget number acquire point work mass"
WALLET_MNEMONIC_2="veteran try aware erosion drink dance decade comic dawn museum release episode original list ability owner size tuition surface ceiling depth seminar capable only"
WALLET_MNEMONIC_3="vacuum burst ordinary enact leaf rabbit gather lend left chase park action dish danger green jeans lucky dish mesh language collect acquire waste load"
WALLET_MNEMONIC_4="open attitude harsh casino rent attitude midnight debris describe spare cancel crisp olive ride elite gallery leaf buffalo sheriff filter rotate path begin soldier"
RLY_MNEMONIC_1="alley afraid soup fall idea toss can goose become valve initial strong forward bright dish figure check leopard decide warfare hub unusual join cart"
RLY_MNEMONIC_2="record gift you once hip style during joke field prize dust unique length more pencil transfer quit train device arrive energy sort steak upset"

P2PPORT_1=16656
P2PPORT_2=26656
RPCPORT_1=16657
RPCPORT_2=26657
RESTPORT_1=1316
RESTPORT_2=1317
ROSETTA_1=8080
ROSETTA_2=8081

# Stop if it is already running 
if pgrep -x "$BINARY" >/dev/null; then
    echo "Terminating $BINARY..."
    killall $BINARY
fi

echo "Removing previous data..."
rm -rf $CHAIN_DIR/$CHAINID_1 &> /dev/null
rm -rf $CHAIN_DIR/$CHAINID_2 &> /dev/null

# Add directories for both chains, exit if an error occurs
if ! mkdir -p $CHAIN_DIR/$CHAINID_1 2>/dev/null; then
    echo "Failed to create chain folder. Aborting..."
    exit 1
fi

if ! mkdir -p $CHAIN_DIR/$CHAINID_2 2>/dev/null; then
    echo "Failed to create chain folder. Aborting..."
    exit 1
fi

echo "Initializing $CHAINID_1..."
echo "Initializing $CHAINID_2..."
$BINARY init test --home $CHAIN_DIR/$CHAINID_1 --chain-id=$CHAINID_1
$BINARY init test --home $CHAIN_DIR/$CHAINID_2 --chain-id=$CHAINID_2

echo "Adding genesis accounts..."
echo $VAL_MNEMONIC_1 | $BINARY keys add val1 --home $CHAIN_DIR/$CHAINID_1 --recover --keyring-backend=test
echo $VAL_MNEMONIC_2 | $BINARY keys add val2 --home $CHAIN_DIR/$CHAINID_2 --recover --keyring-backend=test
echo $WALLET_MNEMONIC_1 | $BINARY keys add wallet1 --home $CHAIN_DIR/$CHAINID_1 --recover --keyring-backend=test
echo $WALLET_MNEMONIC_2 | $BINARY keys add wallet2 --home $CHAIN_DIR/$CHAINID_1 --recover --keyring-backend=test
echo $WALLET_MNEMONIC_3 | $BINARY keys add wallet3 --home $CHAIN_DIR/$CHAINID_2 --recover --keyring-backend=test
echo $WALLET_MNEMONIC_4 | $BINARY keys add wallet4 --home $CHAIN_DIR/$CHAINID_2 --recover --keyring-backend=test
echo $RLY_MNEMONIC_1 | $BINARY keys add rly1 --home $CHAIN_DIR/$CHAINID_1 --recover --keyring-backend=test 
echo $RLY_MNEMONIC_2 | $BINARY keys add rly2 --home $CHAIN_DIR/$CHAINID_2 --recover --keyring-backend=test 

$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_1 keys show val1 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_1
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_2 keys show val2 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_2
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_1 keys show wallet1 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_1
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_1 keys show wallet2 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_1
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_2 keys show wallet3 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_2
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_2 keys show wallet4 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_2
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_1 keys show rly1 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_1
$BINARY add-genesis-account $($BINARY --home $CHAIN_DIR/$CHAINID_2 keys show rly2 --keyring-backend test -a) 100000000000uumee,100000000000utest  --home $CHAIN_DIR/$CHAINID_2

echo "Creating and collecting gentx..."
$BINARY gentx-gravity val1 7000000000uumee 0x0Ca2adaC7e34EF5db8234bE1182070CD980273E8 umee1s9lg2vpjrwmyn93ftzkpkr750xjwzdp7a6e97h --home $CHAIN_DIR/$CHAINID_1 --chain-id $CHAINID_1 --keyring-backend test
$BINARY gentx-gravity val2 7000000000uumee 0x17B9E914a10f0b1Cf4684781fBaC9358e56d0282 umee1yfrk6yw6uwu8srhd6txz5rec7rsxpjnvdtztxx --home $CHAIN_DIR/$CHAINID_2 --chain-id $CHAINID_2 --keyring-backend test
$BINARY collect-gentxs --home $CHAIN_DIR/$CHAINID_1
$BINARY collect-gentxs --home $CHAIN_DIR/$CHAINID_2
$BINARY validate-genesis --home $CHAIN_DIR/$CHAINID_1
$BINARY validate-genesis --home $CHAIN_DIR/$CHAINID_2

echo "Changing defaults and ports in app.toml and config.toml files..."
sed -i -e 's#"tcp://0.0.0.0:26656"#"tcp://0.0.0.0:'"$P2PPORT_1"'"#g' $CHAIN_DIR/$CHAINID_1/config/config.toml
sed -i -e 's#"tcp://127.0.0.1:26657"#"tcp://0.0.0.0:'"$RPCPORT_1"'"#g' $CHAIN_DIR/$CHAINID_1/config/config.toml
sed -i -e 's/timeout_commit = "5s"/timeout_commit = "1s"/g' $CHAIN_DIR/$CHAINID_1/config/config.toml
sed -i -e 's/timeout_propose = "3s"/timeout_propose = "1s"/g' $CHAIN_DIR/$CHAINID_1/config/config.toml
sed -i -e 's/index_all_keys = false/index_all_keys = true/g' $CHAIN_DIR/$CHAINID_1/config/config.toml
sed -i -e 's/enable = false/enable = true/g' $CHAIN_DIR/$CHAINID_1/config/app.toml
sed -i -e 's/swagger = false/swagger = true/g' $CHAIN_DIR/$CHAINID_1/config/app.toml
sed -i -e 's#"tcp://0.0.0.0:1317"#"tcp://0.0.0.0:'"$RESTPORT_1"'"#g' $CHAIN_DIR/$CHAINID_1/config/app.toml
sed -i -e 's#":8080"#":'"$ROSETTA_1"'"#g' $CHAIN_DIR/$CHAINID_1/config/app.toml
sed -i -e 's/minimum-gas-prices = ""/minimum-gas-prices = "0.0001uumee"/g' $CHAIN_DIR/$CHAINID_1/config/app.toml

sed -i -e 's#"tcp://0.0.0.0:26656"#"tcp://0.0.0.0:'"$P2PPORT_2"'"#g' $CHAIN_DIR/$CHAINID_2/config/config.toml
sed -i -e 's#"tcp://127.0.0.1:26657"#"tcp://0.0.0.0:'"$RPCPORT_2"'"#g' $CHAIN_DIR/$CHAINID_2/config/config.toml
sed -i -e 's/timeout_commit = "5s"/timeout_commit = "1s"/g' $CHAIN_DIR/$CHAINID_2/config/config.toml
sed -i -e 's/timeout_propose = "3s"/timeout_propose = "1s"/g' $CHAIN_DIR/$CHAINID_2/config/config.toml
sed -i -e 's/index_all_keys = false/index_all_keys = true/g' $CHAIN_DIR/$CHAINID_2/config/config.toml
sed -i -e 's/enable = false/enable = true/g' $CHAIN_DIR/$CHAINID_2/config/app.toml
sed -i -e 's/swagger = false/swagger = true/g' $CHAIN_DIR/$CHAINID_2/config/app.toml
sed -i -e 's#"tcp://0.0.0.0:1317"#"tcp://0.0.0.0:'"$RESTPORT_2"'"#g' $CHAIN_DIR/$CHAINID_2/config/app.toml
sed -i -e 's#":8080"#":'"$ROSETTA_2"'"#g' $CHAIN_DIR/$CHAINID_2/config/app.toml
sed -i -e 's/minimum-gas-prices = ""/minimum-gas-prices = "0.0001uumee"/g' $CHAIN_DIR/$CHAINID_2/config/app.toml


echo "Changing the uibc params for testing... TOKEN_QUOTA=100"
jq .app_state.uibc.params.token_quota=\"100\" $CHAIN_DIR/$CHAINID_1/config/genesis.json > /tmp/genesis.json
mv /tmp/genesis.json $CHAIN_DIR/$CHAINID_1/config/genesis.json
echo "new token_quota => $(jq .app_state.uibc.params.token_quota $CHAIN_DIR/$CHAINID_1/config/genesis.json)"


price_feeder_set_config() {
    RPC=16657
    GRPC=8090
    PF_PORT=7171
    ACCT_NUM=$(($VAL_NUM + 2))

    # Copy the price-feeder config template and replace variables
    CONFIG_DIR=$CHAIN_DIR/$CHAINID_1/config
    PF_CONFIG="${CONFIG_DIR}/price-feeder.toml"
    cp ./scripts/configs/price-feeder.toml $PF_CONFIG
    PRICE_FEEDER_VALIDATOR="$(umeed keys show val1 --home $CHAIN_DIR/$CHAINID_1 --bech val --keyring-backend test -a)"
    # PRICE_FEEDER_VALIDATOR=$(eval "umeed keys show validator${VAL_NUM} --home ${DAEMON_HOME}-${VAL_NUM} --bech val --keyring-backend test --output json | jq .address")
    PRICE_FEEDER_ADDRESS="$(umeed keys show wallet1 --home $CHAIN_DIR/$CHAINID_1 --keyring-backend test -a)"
    # PRICE_FEEDER_ADDRESS="\"$(eval "umeed keys show account${ACCT_NUM} -a --home $DAEMON_HOME-1 --keyring-backend test")\""
    UMEE_VAL_KEY_DIR=$CHAIN_DIR/$CHAINID_1
    UMEE_VAL_HOST="tcp://localhost:${RPC}"

    sed -i -e "s/\$PF_PORT/${PF_PORT}/g" $PF_CONFIG
    sed -i -e "s/\"\$PRICE_FEEDER_VALIDATOR\"/\"${PRICE_FEEDER_VALIDATOR}\"/g" $PF_CONFIG
    sed -i -e "s/\"\$PRICE_FEEDER_ADDRESS\"/\"${PRICE_FEEDER_ADDRESS}\"/g" $PF_CONFIG
    sed -i -e "s|\"\$UMEE_VAL_KEY_DIR\"|\"${UMEE_VAL_KEY_DIR}\"|g" $PF_CONFIG
    sed -i -e "s/\$GRPC/${GRPC}/" $PF_CONFIG
    sed -i -e "s/\$RPC/${RPC}/" $PF_CONFIG
    sed -i -e "s/chain_id = \"test\"/chain_id = \"$CHAINID_1\"/g" $PF_CONFIG
}

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Setting the price-feeder config"
price_feeder_set_config