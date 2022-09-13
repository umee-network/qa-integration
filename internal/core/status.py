from asyncio import as_completed
import concurrent.futures
from time import sleep
from threading import Thread
from utils import env, exec_command

DAEMON = env.DAEMON
NUM_VALS = env.NUM_VALS
STARTING_RPC_PORT = 16657
NUM_RETRIES = 10

# wait_for_node_status checks every three seconds to see if the node 
# is running and has started to produce blocks a maximum of 20 times
def wait_for_node_status(rpc_url, val_num):
    for i in range(NUM_RETRIES):
        sleep(3)
        command = f"{DAEMON} status --node {rpc_url}"
        status, response = exec_command(command)
        if not status:
            print(f"validator{val_num} node {rpc_url} is not responding: waiting 3 seconds; {NUM_RETRIES-i-1} tries remaining")
            continue
        block_height = int(response['SyncInfo']['latest_block_height'])
        if block_height > 0:
            print(f"validator{val_num} node {rpc_url} online with block_height: {block_height}")
            return True, ""
        print(f"validator{val_num} node {rpc_url} block height is at zero: waiting 3 seconds; {NUM_RETRIES-i-1} tries remaining")
    return False, f"validator{val_num} node {rpc_url} did not start"

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = []
    for i in range(NUM_VALS):
        rpc_port = STARTING_RPC_PORT + (i * 2)
        rpc_url = f"http://localhost:{rpc_port}"
        futures.append(executor.submit(wait_for_node_status, rpc_url, i+1))
    for future in concurrent.futures.as_completed(futures):
        success, error_message = future.result()
        if not success:
            raise Exception(error_message)
