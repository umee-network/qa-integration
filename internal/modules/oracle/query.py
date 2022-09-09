import time
from utils import exec_command, env

DAEMON = env.DAEMON
RPC = env.RPC
CHAINID = env.CHAINID
BLOCKS_PER_VOTING_PERIOD = 5

# query_exchange_rates queries the prices of all exchange rates
def query_exchange_rates():
    command = f"""{DAEMON} q oracle exchange-rates --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_exchange_rate queries the price of an exchange rate
def query_exchange_rate(asset):
    command = f"""{DAEMON} q oracle exchange-rate {asset} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def query_aggregate_prevote(valAddress):
    command = f"""{DAEMON} q oracle aggregate-prevotes {valAddress} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def query_aggregate_vote(valAddress):
    command = f"""{DAEMON} q oracle aggregate-votes {valAddress} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def query_feeder_delegation(valAddress):
    command = f"""{DAEMON} q oracle feeder-delegation {valAddress} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def query_miss_counter(valAddress):
    command = f"""{DAEMON} q oracle miss-counter {valAddress} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def query_params():
    command = f"""{DAEMON} q oracle params --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

def node_status():
    command = f"{DAEMON} status --node {RPC}"
    return exec_command(command)

def get_block_height():
    _, message = node_status()
    return message["SyncInfo"]["latest_block_height"]

def blocks_until_next_voting_period(block_height):
    vp_block_height = (block_height % BLOCKS_PER_VOTING_PERIOD)
    return BLOCKS_PER_VOTING_PERIOD - vp_block_height

def wait_for_next_voting_period(block_height=None):
    block_height = block_height or int(get_block_height())
    blocks = blocks_until_next_voting_period(block_height)
    if blocks < 5:
        time.sleep(blocks / 2)
