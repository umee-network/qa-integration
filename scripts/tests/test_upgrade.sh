#/bin/sh

## This script creates the necessary folders for cosmovisor. It also builds and places
## the binaries in the folders depending on the upgrade name.

set -e

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
echo $CURPATH
cd $CURPATH

# check environment variables are set
. ../deps/env-check.sh

# NUM_VALS represents number of validator nodes
NUM_VALS=$1
if [ -z $NUM_VALS ]
then
    NUM_VALS=2
fi

if [ -z $UPGRADE_WAITING_TIME ]
then
    UPGRADE_WAITING_TIME=10
fi

cd $CURPATH

# testing all txs and queries
# bash ./all_modules.sh

echo "INFO: Building binary with upgrade version: $UPGRADE_VERSION"
cd $HOME
export REPO=$(basename $GH_URL .git)
if [ ! -d $REPO ]
then
    git clone $GH_URL $REPO
fi
cd $REPO
echo "Checking out new upgrade verison $UPGRADE_VERSION"
git fetch --all && git checkout $UPGRADE_VERSION && git branch --show-current
make build
for (( a=1; a<=$NUM_VALS; a++ ))
do
    export DAEMON_HOME_$a=$DAEMON_HOME-$a
    mkdir -p "$DAEMON_HOME-$a"/cosmovisor/upgrades/$UPGRADE_NAME/bin
    cp ~/$REPO/build/$DAEMON "$DAEMON_HOME-$a"/cosmovisor/upgrades/$UPGRADE_NAME/bin/
done

CURRENT_BLOCK_HEIGHT=$(curl $RPC/status -s | jq .result.sync_info.latest_block_height -r)
echo "INFO: Current Block Height $CURRENT_BLOCK_HEIGHT"
echo "INFO: Submitting software upgrade proposal for upgrade: $UPGRADE_NAME and \
    BLOCK HEIGHT : $(($CURRENT_BLOCK_HEIGHT + 60))"

$DAEMON tx gov submit-proposal software-upgrade $UPGRADE_NAME --title $UPGRADE_NAME \
    --description upgrade --upgrade-height $(($CURRENT_BLOCK_HEIGHT + 60)) --deposit 10000000$DENOM \
    --from validator1 --yes --keyring-backend test --home $DAEMON_HOME-1 --node $RPC --chain-id \
    $CHAINID -b block --fees $DEFAULT_FEES

sleep 4

PROPOSAL_ID=`$DAEMON q gov proposals --status voting_period -o json --node $RPC | \
jq -c '.proposals | .[] | select(.content.title == '\"$UPGRADE_NAME\"') | .proposal_id | tonumber'`

echo "INFO: Voting on created proposal , PROPOSAL_ID=$PROPOSAL_ID"
for (( a=1; a<=$NUM_VALS; a++ ))
do
    $DAEMON tx gov vote $PROPOSAL_ID yes --from validator$a --yes --keyring-backend test \
    --home $DAEMON_HOME-$a --node $RPC --chain-id $CHAINID -b block --fees $DEFAULT_FEES
done

echo "INFO: Waiting for proposal to pass and upgrade"
sleep 60

echo "INFO: Waiting for upgrade setup"
sleep $UPGRADE_WAITING_TIME

# count=0
# while [[ count -le 5 ]]; do
#     CURRENT_VERSION=$(curl -s "$RPC/abci_query?path=%22/app/version%22" | jq -r '.result.response.value' | base64 -d && echo)
#     echo "CURRENT_VERSION $CURRENT_VERSION"
#     # if [ "v$CURRENT_VERSION" = "$UPGRADE_VERSION" ]; then
#     #     break
#     # fi
#     count=$((count+1))
#     sleep 20s
# done

# if [[ $count -eq 6 ]]; then
#     echo "ERROR: Upgrade failed with binary issues"
#     exit 1
# fi

echo "Checking the $UPGRADE with staking validator commission rate"
MIN_COMMISSION_RATE=0.050000000000000000
## Fetching validator commission rate 
VAL1_OPERATOR_ADDR=$($DAEMON q staking validators --node $RPC -o json | jq -c '.validators | .[] | select(.description.moniker == '\"validator-1\"') | .operator_address' | jq -r )
VAL1_COMMISSION_RATE=$($DAEMON q staking validator $VAL1_OPERATOR_ADDR --node http://localhost:16657 -o json  | jq .commission.commission_rates.rate | jq -r )

echo $VAL1_COMMISSION_RATE
if [[ "$VAL1_COMMISSION_RATE" == "$MIN_COMMISSION_RATE" ]];then
    echo "👍 INFO: Upgrade done successfully"
else
    echo "👎🏻 INFO: Upgrade faiiled, Please check binaries or proposal"
fi
