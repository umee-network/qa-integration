#! /bin/bash 

# Variables...
BINARY=$1
VAL_ADDR=$($BINARY keys show val1 --home ./data/test-1 --keyring-backend test -a)
RECV_ADDR=$($BINARY keys show val2 --home ./data/test-2 --keyring-backend test -a)


echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making non-supported token registry ibc-transfer transaction..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
do_non_reg_token() {
    echo "Non register token : IBC Transfer from val1 to receiver $RECV_ADDR and amount 100000000utest"
    RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000utest --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
    if [ $RESPC_CODE -eq 0 ];then
        echo "✅ Successfully ibc-transfer txs is done for non-suported token registry."
    else
        echo "❌ ibc-transfer txs is failed for non-suported token registry."
        echo "ℹ️ retryng again.."
        do_non_reg_token
    fi
}
do_non_reg_token

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making ibc-transfer transaction..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
do_reg_token(){
    echo "Register token (Quota): IBC Transfer from val1 to receiver $RECV_ADDR and amount 100000000uumee"
    RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000uumee --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
    if [ $RESPC_CODE -eq 0 ];then
        echo "✅ Successfully initial ibc-transfer txs is done"
    else
        echo "❌ ibc-transfer txs is failed."
        echo "ℹ️ retrying again.."
        do_reg_token
    fi
}
do_reg_token

sleep 3
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "After ibc-transfer transaction sender $VAL_ADDR bank balance..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$BINARY q bank balances $VAL_ADDR --node tcp://localhost:16657 -o json | jq .

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "After ibc-transfer transaction checking bank balances of receiver $RECV_ADDR on second chain..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$BINARY q bank balances $RECV_ADDR --node tcp://localhost:26657 -o json | jq .

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Checking the ibc-transfer on second chain $RECV_ADDR ..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
RECV_AMOUNT=$($BINARY q bank balances $RECV_ADDR --denom ibc/9F53D255F5320A4BE124FF20C29D46406E126CE8A09B00CA8D3CFF7905119728 --node tcp://localhost:26657 -o json | jq .amount -r)
if [ $RECV_AMOUNT -eq 100000000 ];then
    echo "✅ Successfully initial ibc-transfer received on second chain."
else
    echo "❌ amount is not received on second chain."
fi

RECV_AMOUNT=$($BINARY q bank balances $RECV_ADDR --denom ibc/420D174441F6BE5B2469E6956F61482B88F39E3E86FD79ABF43C9617897388B6 --node tcp://localhost:26657 -o json | jq .amount -r)
if [ $RECV_AMOUNT -eq 100000000 ];then
    echo "✅ Successfully initial ibc-transfer received on second chain."
else
    echo "❌ amount is not received on second chain."
fi


echo "Tests for quotas"
$BINARY q uibc outflows --node tcp://localhost:16657 -o json | jq .

echo "Tests for get quota of denom"
$BINARY q uibc outflows uumee --node tcp://localhost:16657 -o json | jq .

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making second ibc-transfer transaction to check ibc-transfer quota..."
echo "To test for every 1 minute, we are allowing only 100$ to each denom"
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
do_tx(){
    RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 12000000000uumee --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
    if [ $RESPC_CODE -ne 0 ];then
        echo "✅ Successfully checked ibc-transfer quota"
    else
        echo "❌ ibc-transfer quota checking is failed."
        echo "ℹ️ retrying again.."
        do_tx
    fi
}
do_tx

echo "Get all quotas"
$BINARY q uibc outflows --node tcp://localhost:16657 -o json | jq .
echo "Get Umee quota"
$BINARY q uibc outflows uumee --node tcp://localhost:16657 -o json | jq .
# Sleep 60s to check the quota is reset or not? 
echo "Sleep for 60s to check the quota is reset or not..."
sleep 60

echo "Reset quotas..."
RESET=$($BINARY q uibc outflows uumee --node tcp://localhost:16657 -o json  | jq .outflows | jq ".[].amount | tonumber")
echo "Reset quota amount $RESET"

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Stopping the umeed and hermes process"
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
killall -e umeed 
killall -e price-feeder umeed hermes
sleep 5
rm -rf ./data