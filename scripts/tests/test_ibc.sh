
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Init the two chains..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bash ./scripts/chain/ibc/hermes-relayer/init_chains.sh umeed
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Start the two chains..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bash ./scripts/chain/ibc/hermes-relayer/start_chains.sh umeed
sleep 10
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Setup the hermes relayer config..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bash ./scripts/chain/ibc/hermes-relayer/hermes/restore_keys.sh
bash ./scripts/chain/ibc/hermes-relayer/hermes/create_conn.sh

echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo "Starting the hermes-relayer..."
echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
touch ./data/hermes.log
bash ./scripts/chain/ibc/hermes-relayer/hermes/start_relayer.sh > ./data/hermes.log 2>&1 &
sleep 10 

bash ./scripts/chain/ibc/hermes-relayer/ibc_txs.sh umeed
