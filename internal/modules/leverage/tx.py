from utils import exec_command, env

DAEMON = env.DAEMON
DAEMON_HOME = env.DAEMON_HOME
RPC = env.RPC
CHAINID = env.CHAINID
DEFAULT_GAS = env.DEFAULT_GAS

# tx_supply submits a supply tx given a supplier and an amount
def tx_supply(
    from_key,
    supplier,
    amount,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage supply {supplier} {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_withdraw submits a withdraw tx given a supplier and an amount
def tx_withdraw(
    from_key,
    supplier,
    amount,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage withdraw {supplier} {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_collateralize submits a collateralize tx given a borrower and a coin
def tx_collateralize(
    from_key,
    borrower,
    coin,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage collateralize {borrower} {coin} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_decollateralize submits a decollateralize tx given a borrower and a coin
def tx_decollateralize(
    from_key,
    borrower,
    coin,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage decollateralize {borrower} {coin} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_borrow submits a borrow tx given a borrower and an amount
def tx_borrow(
    from_key,
    borrower,
    amount,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage borrow {borrower} {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_repay submits a repay tx given a borrower and an amount
def tx_repay(
    from_key,
    borrower,
    amount,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage repay {borrower} {amount} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_liquidate submits a liquidate tx given a liquidator, borrower,
# amount, and reward_denom
def tx_liquidate(
    from_key,
    liquidator,
    borrower,
    amount,
    reward_denom,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage liquidate {liquidator} {borrower} {amount} {reward_denom} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)

# tx_update_registry submits a repay tx given a propasal_file and a deposit
def tx_update_registry(
    from_key,
    propasal_file,
    deposit,
    home,
    gas=DEFAULT_GAS,
):
    command = f"""{DAEMON} tx leverage update-registry {propasal_file} {deposit} \
--chain-id {CHAINID} --keyring-backend test \
--home {home} --from {from_key} --node {RPC} --output json -y --gas {gas}"""
    return exec_command(command)
