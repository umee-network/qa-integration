from utils import exec_command, env

DAEMON = env.DAEMON
DAEMON_HOME = env.DAEMON_HOME
RPC = env.RPC
CHAINID = env.CHAINID
DEFAULT_GAS = env.DEFAULT_GAS
DEFAULT_GAS_PRICES = env.DEFAULT_GAS_PRICES
DEFAULT_BROADCAST_MODE = "block"
DEFAULT_FEES  = env.DEFAULT_FEES

# tx_supply submits a supply tx given a supplier and an amount
def tx_supply(
    from_key,
    amount,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage supply {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    print(command)
    return exec_command(command)

# tx_withdraw submits a withdraw tx given a supplier and an amount
def tx_withdraw(
    from_key,
    amount,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage withdraw {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_collateralize submits a collateralize tx given a borrower and a coin
def tx_collateralize(
    from_key,
    coin,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage collateralize {coin} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_decollateralize submits a decollateralize tx given a borrower and a coin
def tx_decollateralize(
    from_key,
    coin,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage decollateralize {coin} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_borrow submits a borrow tx given a borrower and an amount
def tx_borrow(
    from_key,
    amount,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage borrow {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_repay submits a repay tx given a borrower and an amount
def tx_repay(
    from_key,
    amount,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage repay {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_liquidate submits a liquidate tx given a liquidator, borrower,
# amount, and reward_denom
def tx_liquidate(
    from_key,
    borrower,
    amount,
    reward_denom,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage liquidate {borrower} {amount} {reward_denom} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)

# tx_update_registry submits a repay tx given a propasal_file and a deposit
def tx_update_registry(
    from_key,
    propasal_file,
    deposit,
    home,
    broadcast_mode=DEFAULT_BROADCAST_MODE,
    gas=DEFAULT_GAS,
    gp=DEFAULT_GAS_PRICES,
):
    command = f"""{DAEMON} tx leverage update-registry {propasal_file} {deposit} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas} --gas-prices {gp} -b {broadcast_mode} --fees {DEFAULT_FEES}"""
    return exec_command(command)
