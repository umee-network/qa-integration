from utils import exec_command, env

DAEMON = env.DAEMON
DAEMON_HOME = env.DAEMON_HOME
RPC = env.RPC
CHAINID = env.CHAINID
DEFAULT_GAS = env.DEFAULT_GAS

# tx_submit_prevote submits an aggregate prevote tx given a hash and
# feeder address.
def tx_submit_prevote(
    from_key,
    hash,
    home,
    broadcast_mode='block',
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx oracle exchange-rate-prevote {hash} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} -b {broadcast_mode}"""
    return exec_command(command)

# tx_submit_vote submits an aggregate vote tx given a salt, exchange
# rates, and a feeder address.
def tx_submit_vote(
    from_key,
    salt,
    home,
    exchange_rates,
    broadcast_mode='block',
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx oracle exchange-rate-vote {salt} {exchange_rates} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} -b {broadcast_mode}"""
    return exec_command(command)
