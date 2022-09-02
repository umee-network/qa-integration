from utils import exec_command, env

DAEMON = env.DAEMON
DAEMON_HOME = env.DAEMON_HOME
RPC = env.RPC
CHAINID = env.CHAINID
DEFAULT_GAS = env.DEFAULT_GAS
DEFAULT_BROADCAST_MODE = "block"

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
