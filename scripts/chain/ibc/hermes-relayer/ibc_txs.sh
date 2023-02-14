#! /bin/bash 

# Variables...
BINARY=$1
VAL_ADDR=$($BINARY keys show val1 --home ./data/test-1 --keyring-backend test -a)
RECV_ADDR=$($BINARY keys show val2 --home ./data/test-2 --keyring-backend test -a)


echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making non-supported token registry ibc-transfer transaction..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000utest --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
if [ $RESPC_CODE -eq 0 ];then
    echo "✅ Successfully ibc-transfer txs is done for non-suported token registry."
else
    echo "❌ ibc-transfer txs is failed for non-suported token registry."
fi

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making ibc-transfer transaction..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# $BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000uumee --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json
RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000uumee --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
if [ $RESPC_CODE -eq 0 ];then
    echo "✅ Successfully initial ibc-transfer txs is done"
else
    echo "❌ ibc-transfer txs is failed."
fi

sleep 3
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "After ibc-transfer transaction bank balances..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$BINARY q bank balances $VAL_ADDR --node tcp://localhost:16657 -o json | jq .

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "After ibc-transfer transaction checking bank balances of receiver on second chain..."
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



echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Making second ibc-transfer transaction to check ibc-transfer quota..."
echo "Every 24hours, we are allowing only 100 tokens to each denom"
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
RESPC_CODE=$($BINARY tx ibc-transfer transfer transfer channel-0 $RECV_ADDR 100000000uumee --chain-id test-1 --node tcp://localhost:16657 --from val1 --home ./data/test-1 --keyring-backend test --fees 2000uumee -y -b block -o json | jq .code -r)
if [ $RESPC_CODE -ne 0 ];then
    echo "✅ Successfully checked ibc-transfer quota"
else
    echo "❌ ibc-transfer quota checking is failed."
fi

echo "Tests for quotas"
$BINARY q uibc quota --node tcp://localhost:16657 -o json | jq .

echo "Tests for get quota of denom"
$BINARY q uibc quota uumee --node tcp://localhost:16657 -o json | jq .

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Stopping the umeed and hermes process"
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
killall -e umeed 
killall -e hermes
sleep 5
rm -rf ./data
