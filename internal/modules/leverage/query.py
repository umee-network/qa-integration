"""
Querying functions for the leverage module.
"""

from internal.utils import exec_command, env

DAEMON = env.DAEMON
RPC = env.RPC
CHAINID = env.CHAINID

# query_params quieries the leverage module parameters
def query_params():
    command = f"{DAEMON} q leverage params --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_registered_tokens quieries for all the current registered tokens
def query_registered_tokens():
    command = f"{DAEMON} q leverage registered-tokens --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_market_summary quieries for the market summary of a specified denomination
def query_market_summary(denom):
    command = f"{DAEMON} q leverage market-summary {denom} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_account_balances quieries for the total supplied, collateral, and borrowed tokens for an address
def query_account_balances(addr):
    command = f"{DAEMON} q leverage account-balances {addr} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_account_summary for position USD values and borrowing limits for an address
def query_account_summary(addr):
    command = f"{DAEMON} q leverage account-summary {addr} --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)

# query_liquidation_targets quieries for all borrower addresses eligible for liquidation
def query_liquidation_targets():
    command = f"{DAEMON} q leverage liquidation-targets --node {RPC} \
--chain-id {CHAINID} --output json"""
    return exec_command(command)