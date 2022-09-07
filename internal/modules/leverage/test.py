import time
import logging
import unittest
import inspect
import pathlib
import threading
import random
from utils import env

from internal.modules.oracle.query import (
    query_aggregate_vote,
    node_status,
)
from modules.oracle.tx import (
    tx_submit_prevote,
    tx_submit_vote,
)
from modules.oracle.hash import (
    get_hash,
)
from modules.oracle.rates import (
    ExchangeRates,
    ExchangeRate,
)
EXCHANGE_RATES = ExchangeRates(
    ExchangeRate("UMEE", "0.02"),
    ExchangeRate("ATOM", "1.00"),
    ExchangeRate("JUNO", "0.50"),
)
UPDATED_EXCHANGE_RATES = ExchangeRates(
    ExchangeRate("UMEE", "0.02"),
    ExchangeRate("ATOM", "2.00"),
    ExchangeRate("JUNO", "0.70"),
)

from modules.leverage.query import (
    query_registered_tokens,
)
from modules.leverage.tx import (
    tx_supply,
    tx_withdraw,
    tx_collateralize,
    tx_borrow,
    tx_repay,
)

BLOCKS_PER_VOTING_PERIOD = 5
STATIC_SALT = "af8ed1e1f34ac1ac00014581cbc31f2f24480b09786ac83aabf2765dada87509"

from internal.core.keys import keys_show
from internal.modules.gov.tx import submit_and_pass_proposal
from internal.modules.bank.query import query_balances

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

validator1_home = f"{env.DAEMON_HOME}-1"
validator2_home = f"{env.DAEMON_HOME}-2"

validator1_acc = keys_show("validator1", "val")[1]
validator2_val = keys_show("validator2", "val", validator2_home)[1]

accounts = []
for i in range(2):
    acc = keys_show("account" + str(i+1))[1]
    accounts.append(acc)

def get_block_height():
    _, message = node_status()
    return message["SyncInfo"]["latest_block_height"]

def wait_for_next_voting_period():
    block_height = int(get_block_height())
    vp_block_height = (block_height % BLOCKS_PER_VOTING_PERIOD)
    if vp_block_height > 0:
        time.sleep((BLOCKS_PER_VOTING_PERIOD - vp_block_height) / 2)

class TestLeverageModuleTxsQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        update_registry_path = pathlib.Path().resolve().joinpath("./internal/modules/leverage/update-token-registry.json")
        submit_and_pass_proposal(
            proposal_file_or_name=update_registry_path,
            proposal_type='update-registry'
        )
        time.sleep(20)

    def exchange_rate_set(self, exchange_rates, stop):
        while True:
            # Get Hash
            vote_hash = get_hash(exchange_rates.ToString(), STATIC_SALT, validator2_val["address"])

            wait_for_next_voting_period()

            # Submit prevote
            status, prevote_1 = tx_submit_prevote(validator2_val["name"], vote_hash, validator2_home)
            self.assertTrue(status)

            time.sleep(1.5) # Wait until next voting period

            # Submit vote
            status, vote_1 = tx_submit_vote(validator2_val["name"], STATIC_SALT, validator2_home, exchange_rates.ToString())
            self.assertTrue(status)

            # Query votes to make sure they exist, and are correct
            status, vote_1 = query_aggregate_vote(validator2_val["address"])
            self.assertTrue(status)

            self.assertEqual(len(vote_1["aggregate_vote"]["exchange_rate_tuples"]), exchange_rates.Len())

            for rate in vote_1["aggregate_vote"]["exchange_rate_tuples"]:
                self.assertEqual(float(rate["exchange_rate"]), float(exchange_rates.GetRate(rate["denom"])))

            if stop():
                break

    def assert_equal_balances(self, acc_balance, denom_amounts):
        i = 0
        for denom, amount in denom_amounts.items():
            self.assertEqual(acc_balance["balances"][i]["denom"], denom)
            self.assertEqual(acc_balance["balances"][i]["amount"], amount)
            i+=1

    def supply_and_collateralize(self, account_name, account_address, supply_amount, collateralize_amount, validator_home):
        status = tx_supply(account_name, account_address, supply_amount, validator_home)
        self.assertTrue(status)
        status = tx_collateralize(account_name, account_address, collateralize_amount, validator_home)
        self.assertTrue(status)

    def batch_borrow(self, first_account, last_account, amount, validator_home):
        for i in range(first_account, last_account):
            status = tx_borrow(accounts[i]["name"], accounts[i]["address"], amount, validator_home)
            self.assertTrue(status)

    def supply_or_withdraw(self):
        supply = random.choice([True, False])
        if supply:
            status = tx_supply(accounts[0]["name"], accounts[0]["address"], "1000000uumee", validator1_home)
            self.assertTrue(status)
        else:
            status = tx_withdraw(accounts[0]["name"], accounts[0]["address"], "1000000u/uumee", validator1_home)
            self.assertTrue(status)

    def test_query_total_supply(self):
        status, res = query_registered_tokens()
        self.assertTrue(status)
        self.assertTrue(len(res['registry']) == 3, "It should have three tokens registered")

    def test_supply_withdraw(self):
        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of supply/withdraw test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies between 10% and 90% of their uumee balance
        status = tx_supply(accounts[0]["name"], accounts[0]["address"], "500000000000uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # Query User A bank balance of u/uumee
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying 500000 umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','u/uumee':'500000000000','uumee':'500000000000'})

        # User A withdraws between 10% and 90% of their u/uumee balance
        status = tx_withdraw(accounts[0]["name"], accounts[0]["address"], "500000000000u/uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after withdrawing 500000 u/umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

    def test_supply_withdraw_atom(self):
        # Query User A bank balance of atom
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of supply/withdraw atom test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies between 10% and 90% of their atom balance
        status = tx_supply(accounts[0]["name"], accounts[0]["address"], "5000000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # Query User A bank balance of u/ibc/atom
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying 5000 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'5000000000','ibc/juno':'20000000000','u/ibc/atom':'5000000000','uumee':'1000000000000'})

        # User A withdraws between 10% and 90% of their u/ibc/atom balance
        status = tx_withdraw(accounts[0]["name"], accounts[0]["address"], "5000000000u/ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # Query User A bank balance of atom
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after withdrawing 5000 u/atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

    def test_simple_functional(self):
        # Submit exhange rates to price feeder every voting period in the background
        stop_exchange_rate_set = False
        exchange_rate_set_thread = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, lambda : stop_exchange_rate_set))
        exchange_rate_set_thread.start()
        wait_for_next_voting_period()

        # Query User A and User B bank balance
        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of simple functional test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})
        status, acc2_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances at start of simple functional test: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies and collaterlizes 10000 umee
        status = tx_supply(accounts[0]["name"], accounts[0]["address"], "10000000000uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(2)
        status = tx_collateralize(accounts[0]["name"], accounts[0]["address"], "10000000000u/uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # User B supplies 2 atom
        status = tx_supply(accounts[1]["name"], accounts[1]["address"], "2000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying and collateralizing 10000 umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after supplying 2 atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9998000000','ibc/juno':'20000000000','u/ibc/atom':'2000000','uumee':'1000000000000'})

        # User A borrows 1 atom
        status = tx_borrow(accounts[0]["name"], accounts[0]["address"], "1000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        # User B withdraws 1 atom
        status = tx_withdraw(accounts[1]["name"], accounts[1]["address"], "1000000u/ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after borrowing 1 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10001000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after withdrawing 1 u/atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9999000000','ibc/juno':'20000000000','u/ibc/atom':'1000000','uumee':'1000000000000'})

        # User A pays back 1 atom
        status = tx_repay(accounts[0]["name"], accounts[0]["address"], "1000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(2)

        status, acc1_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after repaying 1 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts[0]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after acc1 repaid 1 atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9999000000','ibc/juno':'20000000000','u/ibc/atom':'1000000','uumee':'1000000000000'})

        # Stop exhange rate setting thread
        stop_exchange_rate_set = True
        exchange_rate_set_thread.join()

    # def test_supply_or_withdraw(self):


    # def test_functional_one(self):
    #     # Submit exhange rates to price feeder every voting period in the background
    #     stop_exchange_rate_set = False
    #     exchange_rate_set_thread = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, lambda : stop_exchange_rate_set))
    #     exchange_rate_set_thread.start()
    #     wait_for_next_voting_period()

    #     # account1, ..., account50 supply and collateralize 10000 umee
    #     for i in range(50):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "10000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "10000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account51, ..., account100 supply and collateralize 1000 umee
    #     for i in range(50,99):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account101, ..., account200 supply and collateralize 10000 atom and 200 juno
    #     for i in range(100,199):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "200000000ibc/juno", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "200000000u/ibc/juno", validator1_home)
    #         self.assertTrue(status)

    #     time.sleep(10)

    #     # Once the transactions above are done, in parallel, every 1min, 9 times in total,
    #     # acount51, ..., account100 supply and collateralize 1000 umee
    #     supply_amount = "1000000000uumee"
    #     collateralize_amount = "1000000000u/uumee"
    #     for _ in range(8):
    #         for i in range(50,99):
    #             t = threading.Thread(target=self.supply_and_collateralize,
    #             args=(accounts[i]["name"], accounts[i]["address"], supply_amount, collateralize_amount, validator1_home))
    #             t.start()
    #         time.sleep(60)

    #     # In parallel, account1, ..., account20 borrow 10 atom, account21, ..., account40 borrow 100 atom,
    #     # account41, ..., account60 borrow 150 atom, account61, ..., account100 borrow 300 juno
    #     t1 = threading.Thread(target=self.batch_borrow, args=(0, 19, "10000000ibc/atom", validator1_home))
    #     t2 = threading.Thread(target=self.batch_borrow, args=(20, 39, "100000000ibc/atom", validator1_home))
    #     t3 = threading.Thread(target=self.batch_borrow, args=(40, 59, "150000000ibc/atom", validator1_home))
    #     t4 = threading.Thread(target=self.batch_borrow, args=(60, 99, "300000000ibc/juno", validator1_home))
    #     t1.start()
    #     t2.start()
    #     t3.start()
    #     t4.start()
    #     t1.join()
    #     t2.join()
    #     t3.join()
    #     t4.join()

    #     # Stop exhange rate setting thread
    #     stop_exchange_rate_set = True
    #     exchange_rate_set_thread.join()

    #     # Price of atom grows to 2 usd, price of juno grows to 0.7 usd. Restart exchange rate setting with new rates.
    #     stop_exchange_rate_set = False
    #     exchange_rate_set_thread = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES, lambda : stop_exchange_rate_set))
    #     exchange_rate_set_thread.start()
    #     wait_for_next_voting_period()

    #     # Liquidate whatever possible in parallel

    #     # Stop exhange rate setting thread
    #     stop_exchange_rate_set = True
    #     exchange_rate_set_thread.join()

    # def test_functional_two(self):
    #     # Submit exhange rates to price feeder every voting period in the background
    #     stop_exchange_rate_set = False
    #     exchange_rate_set_thread = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, lambda : stop_exchange_rate_set))
    #     exchange_rate_set_thread.start()
    #     wait_for_next_voting_period()

    #     # account1, ..., account50 supply and collateralize 10000 umee
    #     for i in range(50):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "10000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "10000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account51, ..., account100 supply and collateralize 1000 umee
    #     for i in range(50,99):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account101, ..., account200 supply and collateralize 10000 atom and 200 juno
    #     for i in range(100,199):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "200000000ibc/juno", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "200000000u/ibc/juno", validator1_home)
    #         self.assertTrue(status)

    #     time.sleep(10)

    #     # Once the transactions above are done, in parallel, every 1min, 9 times in total,
    #     # acount51, ..., account100 supply and collateralize 1000 umee
    #     supply_amount = "1000000000uumee"
    #     collateralize_amount = "1000000000u/uumee"
    #     for _ in range(8):
    #         for i in range(50,99):
    #             t = threading.Thread(target=self.supply_and_collateralize,
    #             args=(accounts[i]["name"], accounts[i]["address"], supply_amount, collateralize_amount, validator1_home))
    #             t.start()
    #         time.sleep(60)

    #     # In parallel, account1, ..., account20 borrow 10 atom, account21, ..., account40 borrow 100 atom,
    #     # account41, ..., account60 borrow 150 atom, account61, ..., account100 borrow 300 juno, account101,
    #     # ..., account 200 borrow 100 umee
    #     t1 = threading.Thread(target=self.batch_borrow, args=(0, 19, "10000000ibc/atom", validator1_home))
    #     t2 = threading.Thread(target=self.batch_borrow, args=(20, 39, "100000000ibc/atom", validator1_home))
    #     t3 = threading.Thread(target=self.batch_borrow, args=(40, 59, "150000000ibc/atom", validator1_home))
    #     t4 = threading.Thread(target=self.batch_borrow, args=(60, 99, "300000000ibc/juno", validator1_home))
    #     t5 = threading.Thread(target=self.batch_borrow, args=(100, 199, "100000000uumee", validator1_home))
    #     t1.start()
    #     t2.start()
    #     t3.start()
    #     t4.start()
    #     t5.start()
    #     t1.join()
    #     t2.join()
    #     t3.join()
    #     t4.join()
    #     t5.join()

    #     # Stop exhange rate setting thread
    #     stop_exchange_rate_set = True
    #     exchange_rate_set_thread.join()

    #     # Price of atom grows to 2 usd, price of juno grows to 0.7 usd. Restart exchange rate setting with new rates.
    #     stop_exchange_rate_set = False
    #     exchange_rate_set_thread = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES, lambda : stop_exchange_rate_set))
    #     exchange_rate_set_thread.start()
    #     wait_for_next_voting_period()

    #     # Liquidate whatever possible in parallel

    #     # Stop exhange rate setting thread
    #     stop_exchange_rate_set = True
    #     exchange_rate_set_thread.join()

if __name__ == "__main__":
    logging.info("INFO: running leverage module tests")
    test_src = inspect.getsource(TestLeverageModuleTxsQueries)
    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
        test_src.index(f"def {x}") - test_src.index(f"def {y}")
    )
    unittest.main(verbosity=2)
