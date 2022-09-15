NUM_VALS = 3

lint: install-deps
	PYTHONPATH=./internal pylint ./internal

install-deps:
	@bash ./scripts/deps/prereq.sh
	
build-binary:
	@bash ./scripts/chain/build_binary.sh

setup-chain: install-deps build-binary
	@bash ./scripts/chain/setup_chain.sh 5

setup-chain-create-ibc-accs: install-deps build-binary
	@bash ./scripts/chain/setup_chain.sh 5 true true 	

setup-chain-no-pf: install-deps build-binary
	@bash ./scripts/chain/setup_chain.sh 5 false
	@bash ./scripts/chain/start_chain.sh false

setup-chain-no-pf-create-ibc-accs: install-deps build-binary
	@bash ./scripts/chain/setup_chain.sh 5 false true
	@bash ./scripts/chain/start_chain.sh false

# It will setup new chain data to start new chain
setup-and-start-chain: setup-chain start-chain

# It will use previous chain data to start chain 
start-chain: stop-chain
	@bash ./scripts/chain/start_chain.sh true
	@echo "Waiting for chain to start..."
	@sleep 7

pause-chain:
	@bash ./scripts/chain/pause_nodes.sh

resume-chain:
	@bash ./scripts/chain/resume_nodes.sh

# It will reset the chain data
reset-chain:
	@bash ./scripts/chain/reset_chain.sh 

stop-chain:
	@bash ./scripts/chain/shutdown_nodes.sh

test-all: start-and-start-chain
	@bash ./scripts/chain/node_status.sh
	@bash ./scripts/chain/pause_nodes.sh
	@bash ./scripts/chain/resume_nodes.sh

	TEST_TYPE=multi-msg-load bash ./scripts/tests/multi_msg_load.sh
	TEST_TYPE=query-load bash ./scripts/tests/query_load.sh
	TEST_TYPE=send-load bash ./scripts/tests/send_load.sh
	TEST_TYPE=single-msg-load bash ./scripts/tests/single_msg_load.sh
	$(MAKE) stop-chain

test-all-modules: setup-and-start-chain
	@echo "Running all individual module tests..."
	TEST_TYPE=module bash ./scripts/tests/all_modules.sh
	$(MAKE) stop-chain

test-multi-msg: setup-and-start-chain
	@echo "Running multi msg load test..."
	TEST_TYPE=multi-msg-load bash ./scripts/tests/multi_msg_load.sh
	$(MAKE) stop-chain

test-query-load: setup-and-start-chain
	@echo "Running query load test..."
	TEST_TYPE=query-load bash ./scripts/tests/query_load.sh
	$(MAKE) stop-chain

test-send-load: setup-and-start-chain
	@echo "Running send msg load test..."
	TEST_TYPE=send-load bash ./scripts/tests/send_load.sh
	$(MAKE) stop-chain

test-leverage-module: setup-chain-no-pf-create-ibc-accs
	@echo "Running leverage module tests..."
	TEST_TYPE=leverage-module bash ./scripts/tests/leverage_module.sh
	$(MAKE) stop-chain

test-oracle-module: setup-chain-no-pf
	@echo "Running oracle module tests..."
	TEST_TYPE=oracle-module bash ./scripts/tests/oracle_module.sh
	$(MAKE) stop-chain

test-single-msg: setup-and-start-chain
	@echo "Running single msg load test..."
	TEST_TYPE=single-msg-load bash ./scripts/tests/single_msg_load.sh
	$(MAKE) stop-chain

test-upgrade: setup-and-start-chain
	@echo "Running upgrade test..."
	bash ./scripts/tests/test_upgrade.sh $(NUM_VALS)
	$(MAKE) stop-chain
