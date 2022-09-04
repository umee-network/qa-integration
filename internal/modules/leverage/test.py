import time
import logging
import unittest
import inspect
import pathlib
from utils import env
from modules.leverage.query import (
    query_registered_tokens,
)

from modules.leverage.tx import (
    tx_supply,
    tx_withdraw,
    tx_collateralize,
    tx_borrow,
    tx_repay
)
from internal.core.keys import keys_show
from internal.modules.gov.tx import submit_and_pass_proposal
from internal.modules.bank.query import query_balances

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

validator1_home = f"{env.DAEMON_HOME}-1"

validator1_acc = keys_show("validator1", "val")[1]

accounts = []
for i in range(2):
    acc = keys_show("account" + str(i+1))[1]
    accounts.append(acc)

class TestLeverageModuleTxsQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        update_registry_path = pathlib.Path().resolve().joinpath("./internal/modules/leverage/update-token-registry.json")
        submit_and_pass_proposal(
            proposal_file_or_name=update_registry_path,
            proposal_type='update-registry',
            extra_args='200uumee'
        )
        time.sleep(20)

    def assert_equal_balances(self, acc_balance, denom_amounts):
        i = 0
        for denom, amount in denom_amounts.items():
            self.assertEqual(acc_balance["balances"][i]["denom"], denom)
            self.assertEqual(acc_balance["balances"][i]["amount"], amount)
            i+=1

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

    # def test_functional_one(self):
    #     # account1, ..., account50 supply and collateralize 10000 umee
    #     for i in range(50):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "10000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "10000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account51, ..., account100 supply and collateralize 1000 umee
    #     for i in range(50,100):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000uumee", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/uumee", validator1_home)
    #         self.assertTrue(status)

    #     # account101, ..., account200 supply and collateralize 10000 atom and 200 juno
    #     for i in range(100,200):
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "1000000000ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "1000000000u/ibc/atom", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_supply(accounts[i]["name"], accounts[i]["address"], "200000000ibc/juno", validator1_home)
    #         self.assertTrue(status)
    #         status = tx_collateralize(accounts[i]["name"], accounts[i]["address"], "200000000u/ibc/juno", validator1_home)
    #         self.assertTrue(status)

        # time.sleep(10)

if __name__ == "__main__":
    logging.info("INFO: running leverage module tests")
    test_src = inspect.getsource(TestLeverageModuleTxsQueries)
    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
        test_src.index(f"def {x}") - test_src.index(f"def {y}")
    )
    unittest.main(verbosity=2)