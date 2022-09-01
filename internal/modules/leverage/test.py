import time
import logging
import unittest
import inspect
import pathlib
from utils import env
from internal.core.keys import keys_show
from internal.modules.gov.tx import submit_and_pass_proposal
from internal.modules.bank.query import query_balances

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

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

validator1_home = f"{env.DAEMON_HOME}-1"
validator2_home = f"{env.DAEMON_HOME}-2"

validator1_acc = keys_show("validator1", "val")[1]
validator2_acc = keys_show("validator2", "val", validator2_home)[1]

acc1 = keys_show("account1")[1]
acc2 = keys_show("account2")[1]

class TestLeverageModuleTxsQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        update_registry_path = pathlib.Path().resolve().joinpath("./internal/modules/leverage/update-registry-only-umee.json")
        submit_and_pass_proposal(
            proposal_file_or_name=update_registry_path,
            proposal_type='update-registry',
            extra_args='200uumee'
        )
        time.sleep(20)

    def test_query_total_supply(self):
        status, res = query_registered_tokens()
        self.assertTrue(status)
        self.assertTrue(len(res['registry']) == 3, "It should have three tokens registered")

    def test_supply_withdraw(self):
        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance before supply: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")

        # User A supplies between 10% and 90% of their uumee balance
        status = tx_supply(acc1["name"], acc1["address"], "500000000000uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        # Query User A bank balance of u/uumee
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance after supply: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "u/uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "500000000000")
        self.assertEqual(acc1_balance["balances"][3]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][3]["amount"], "500000000000")

        # User A withdraws between 10% and 90% of their u/uumee balance
        status = tx_withdraw(acc1["name"], acc1["address"], "500000000000u/uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance after withdraw: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")

    def test_supply_withdraw_atom(self):
        # Query User A bank balance of atom
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance before supply: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")

        # User A supplies between 10% and 90% of their atom balance
        status = tx_supply(acc1["name"], acc1["address"], "5000000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        # Query User A bank balance of u/uumee
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance after supply: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "5000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "u/ibc/atom")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "5000000000")
        self.assertEqual(acc1_balance["balances"][3]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][3]["amount"], "1000000000000")

        # User A withdraws between 10% and 90% of their u/ibc/atom balance
        status = tx_withdraw(acc1["name"], acc1["address"], "5000000000u/ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        # Query User A bank balance of atom
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance after withdraw: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")

    def test_simple_functional(self):
        # Query User A and User B bank balance
        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance at start of test: ", acc1_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")
        status, acc2_balance = query_balances(acc2["address"])
        self.assertTrue(status)
        print("\nacc2_balance at start of test: ", acc2_balance["balances"])
        self.assertEqual(acc1_balance["balances"][0]["denom"], "ibc/atom")
        self.assertEqual(acc1_balance["balances"][0]["amount"], "10000000000")
        self.assertEqual(acc1_balance["balances"][1]["denom"], "ibc/juno")
        self.assertEqual(acc1_balance["balances"][1]["amount"], "20000000000")
        self.assertEqual(acc1_balance["balances"][2]["denom"], "uumee")
        self.assertEqual(acc1_balance["balances"][2]["amount"], "1000000000000")

        # User A supplies and collaterlizes 10000 umee
        status = tx_supply(acc1["name"], acc1["address"], "10000000000uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(1)
        status = tx_collateralize(acc1["name"], acc1["address"], "10000000000u/uumee", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        # User B supplies 2 atom
        status = tx_supply(acc2["name"], acc2["address"], "2000000ibc/atom", validator1_home)
        self.assertTrue(status)
        time.sleep(1)

        status, acc1_balance = query_balances(acc1["address"])
        self.assertTrue(status)
        print("\nacc1_balance at end of test: ", acc1_balance["balances"])
        status, acc2_balance = query_balances(acc2["address"])
        self.assertTrue(status)
        print("\nacc2_balance at end of test: ", acc2_balance["balances"])


if __name__ == "__main__":
    logging.info("INFO: running leverage module tests")
    test_src = inspect.getsource(TestLeverageModuleTxsQueries)
    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
        test_src.index(f"def {x}") - test_src.index(f"def {y}")
    )
    unittest.main(verbosity=2)