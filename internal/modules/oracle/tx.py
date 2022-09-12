from utils import exec_command, env
from modules.oracle.hash import (
    get_hash,
)
from modules.oracle.query import (
    wait_for_next_voting_period,
)

DAEMON = env.DAEMON
DAEMON_HOME = env.DAEMON_HOME
RPC = env.RPC
CHAINID = env.CHAINID
DEFAULT_GAS = env.DEFAULT_GAS
DEFAULT_BROADCAST_MODE = "block"

STATIC_SALT = "af8ed1e1f34ac1ac00014581cbc31f2f24480b09786ac83aabf2765dada87509"

# tx_submit_prevote submits an aggregate prevote tx given a hash and
# feeder address.
def tx_submit_prevote(
    from_key,
    hash,
    home,
    validator="",
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx oracle exchange-rate-prevote {hash} {validator} \
        --chain-id {CHAINID} --keyring-backend test \
        --home {home} --from {from_key} --node {RPC} --output json \
        --gas {gas} -b {broadcast_mode} -y"""
    return exec_command(command)

# tx_submit_vote submits an aggregate vote tx given a salt, exchange
# rates, and a feeder address.
def tx_submit_vote(
    from_key,
    salt,
    home,
    exchange_rates,
    validator="",
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx oracle exchange-rate-vote {salt} {exchange_rates} {validator} \
        --chain-id {CHAINID} --keyring-backend test \
        --home {home} --from {from_key} --node {RPC} --output json \
        --gas {gas} -b {broadcast_mode} -y"""
    return exec_command(command)

# tx_delegate_feed_consent submits a tx
def tx_delegate_feed_consent(
    operator,
    delegate,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx oracle delegate-feed-consent {operator} {delegate} \
        --chain-id {CHAINID} --keyring-backend test \
        --home {home} --from {operator} --node {RPC} --output json \
        --gas {gas} -b {broadcast_mode} -y"""
    return exec_command(command)

def tx_send_prevote_and_vote(validator, exchange_rates):
    vote_hash = get_hash(exchange_rates.ToString(), STATIC_SALT, validator['address'])
    status, response = tx_submit_prevote(validator["name"], vote_hash, validator['home'])
    if not status:
        return status, response
    wait_for_next_voting_period(int(response['height']))
    return tx_submit_vote(validator["name"], STATIC_SALT, validator['home'], exchange_rates.ToString())
