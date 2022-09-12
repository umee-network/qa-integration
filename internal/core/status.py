from time import sleep
from threading import Thread
from utils import env, exec_command

DAEMON = env.DAEMON
NUM_VALS = env.NUM_VALS
STARTING_RPC_PORT = 16657

# wait_for_node_status checks every three seconds to see if the node 
# is running and has started to produce blocks a maximum of 20 times
def wait_for_node_status(rpc_url, val_num):
    for i in range(20):
        sleep(3)
        command = f"{DAEMON} status --node {rpc_url}"
        status, response = exec_command(command)
        if not status:
            print(f"validator{val_num} node {rpc_url} is not responding: waiting 3 seconds; {20-i-1} tries remaining")
            continue
        block_height = int(response['SyncInfo']['latest_block_height'])
        if block_height > 0:
            print(f"validator{val_num} node {rpc_url} online with block_height: {block_height}")
            return
        print(f"validator{val_num} node {rpc_url} block height is at zero: waiting 3 seconds; {20-i-1} tries remaining")
    print(f"validator{val_num} node {rpc_url} did not start")

threads = []

for i in range(NUM_VALS):
    rpc_port = STARTING_RPC_PORT + (i * 2)
    rpc_url = f"http://localhost:{rpc_port}"
    thread = Thread(target=wait_for_node_status, args=(rpc_url,i+1,))
    threads.append(thread)
    thread.start()

for i in range(NUM_VALS):
    threads[i].join()
