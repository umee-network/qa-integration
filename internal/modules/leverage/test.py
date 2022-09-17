import time
import logging
import unittest
import inspect
import pathlib
import threading
import random
from utils import env

from internal.modules.oracle.query import (
    query_exchange_rates,
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
UPDATED_EXCHANGE_RATES2 = ExchangeRates(
    ExchangeRate("UMEE", "0.04"),
    ExchangeRate("ATOM", "1.00"),
    ExchangeRate("JUNO", "0.50"),
)

from modules.leverage.query import (
    query_registered_tokens,
    query_market_summary,
    query_liquidation_targets,
    query_account_summary,
)
from modules.leverage.tx import (
    tx_supply,
    tx_withdraw,
    tx_collateralize,
    tx_decollateralize,
    tx_borrow,
    tx_repay,
    tx_liquidate,
)

BLOCKS_PER_VOTING_PERIOD = 10
STATIC_SALT = "af8ed1e1f34ac1ac00014581cbc31f2f24480b09786ac83aabf2765dada87509"

from internal.core.keys import keys_show
from internal.modules.gov.tx import submit_and_pass_proposal
from internal.modules.bank.query import query_balances

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

validator1_home = f"{env.DAEMON_HOME}-1"
validator2_home = f"{env.DAEMON_HOME}-2"
validator3_home = f"{env.DAEMON_HOME}-3"

validator1_val = keys_show("validator1", "val", validator1_home)[1]
validator2_val = keys_show("validator2", "val", validator2_home)[1]
validator3_val = keys_show("validator3", "val", validator3_home)[1]

accounts1 = []
for i in range(1, 201):
    acc = keys_show("a_" + str(i))[1]
    accounts1.append(acc)

liquidators1 = []
for i in range(201, 401):
    liq = keys_show("a_" + str(i))[1]
    liquidators1.append(liq)

accounts2 = []
for i in range(401, 601):
    acc = keys_show("a_" + str(i))[1]
    accounts2.append(acc)

liquidators2 = []
for i in range(601, 801):
    liq = keys_show("a_" + str(i))[1]
    liquidators2.append(liq)

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

    def setUp(self):
        self.stop_exchange_rate_set = False

    def tearDown(self):
        self.stop_exchange_rate_set = True
        
    def exchange_rate_set(self, exchange_rates, validator_val, validator_home):
        while True:
            # Get Hash
            vote_hash = get_hash(exchange_rates.ToString(), STATIC_SALT, validator_val["address"])

            # Submit prevote
            i = 0
            while True:
                status = tx_submit_prevote(validator_val["name"], vote_hash, validator_home)
                i += 1
                if status or (i == 20):
                    self.assertTrue(status)
                    break

            # Submit vote
            i = 0
            while True:
                status = tx_submit_vote(validator_val["name"], STATIC_SALT, validator_home, exchange_rates.ToString())
                i += 1
                if status or (i == 20):
                    self.assertTrue(status)
                    break

            if self.stop_exchange_rate_set:
                break

    def assert_equal_balances(self, acc_balance, denom_amounts):
        i = 0
        for denom, amount in denom_amounts.items():
            self.assertEqual(acc_balance["balances"][i]["denom"], denom)
            self.assertEqual(acc_balance["balances"][i]["amount"], amount)
            i+=1

    def assert_equal_summaries(self, acc_summary, summary_amounts):
        self.assertEqual(acc_summary["supplied_value"], summary_amounts["supplied_value"])
        self.assertEqual(acc_summary["collateral_value"], summary_amounts["collateral_value"])
        self.assertEqual(acc_summary["borrowed_value"], summary_amounts["borrowed_value"])
        self.assertEqual(acc_summary["borrow_limit"], summary_amounts["borrow_limit"])
        self.assertEqual(acc_summary["liquidation_threshold"], summary_amounts["liquidation_threshold"])

    def batch_supply(self, accounts, first_account, last_account, amount, validator_home):
        for i in range(first_account, last_account):
            status = tx_supply(accounts[i]["name"], amount, validator_home, 'async')
            self.assertTrue(status)

    def batch_collateralize(self, accounts, first_account, last_account, amount, validator_home):
        for i in range(first_account, last_account):
            status = tx_collateralize(accounts[i]["name"], amount, validator_home, 'async')
            self.assertTrue(status)

    def batch_borrow(self, accounts, first_account, last_account, amount, validator_home):
        for i in range(first_account, last_account):
            status = tx_borrow(accounts[i]["name"], amount, validator_home)
            self.assertTrue(status)

    def batch_liquidate(self, liquidator_accounts, accounts, first_account, last_account, amount, reward_denom, validator_home):
        for i in range(first_account, last_account):
            status = tx_liquidate(liquidator_accounts[i]["name"], accounts[i]["address"], amount, reward_denom, validator_home, 'async')
            self.assertTrue(status)

    def supply_or_withdraw(self, accounts):
        supply = random.choice([True, False])
        if supply:
            status = tx_supply(accounts[0]["name"], "1000000uumee", validator1_home)
            self.assertTrue(status)
        else:
            status = tx_withdraw(accounts[0]["name"], "1000000u/uumee", validator1_home)
            self.assertTrue(status)

    def test_query_total_supply(self):
        status, res = query_registered_tokens()
        self.assertTrue(status)
        self.assertTrue(len(res['registry']) == 3, "It should have three tokens registered")

    GH Issue: https://github.com/umee-network/umee/issues/1307
    def test_supply_withdraw(self):
        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of supply/withdraw test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies between 10% and 90% of their uumee balance
        status = tx_supply(accounts1[0]["name"], "500000000000uumee", validator1_home)
        self.assertTrue(status)

        # Query User A bank balance of u/uumee
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying 500000 umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','u/uumee':'500000000000','uumee':'500000000000'})

        # User A withdraws between 10% and 90% of their u/uumee balance
        status = tx_withdraw(accounts1[0]["name"], "500000000000u/uumee", validator1_home)
        self.assertTrue(status)

        # Query User A bank balance of uumee
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after withdrawing 500000 u/umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

    def test_supply_withdraw_atom(self):
        # Query User A bank balance of atom
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of supply/withdraw atom test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies between 10% and 90% of their atom balance
        status = tx_supply(accounts1[0]["name"], "5000000000ibc/atom", validator1_home)
        self.assertTrue(status)

        # Query User A bank balance of u/ibc/atom
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying 5000 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'5000000000','ibc/juno':'20000000000','u/ibc/atom':'5000000000','uumee':'1000000000000'})

        # User A withdraws between 10% and 90% of their u/ibc/atom balance
        status = tx_withdraw(accounts1[0]["name"], "5000000000u/ibc/atom", validator1_home)
        self.assertTrue(status)

        # Query User A bank balance of atom
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after withdrawing 5000 u/atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

    # GH Issue: https://github.com/umee-network/umee/issues/1210
    def test_simple_functional(self):
        # Submit exhange rates to price feeder every voting period in the background
        exchange_rate_set_thread1 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator1_val, validator1_home))
        exchange_rate_set_thread2 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator2_val, validator2_home))
        exchange_rate_set_thread3 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator3_val, validator3_home))
        exchange_rate_set_thread1.start()
        exchange_rate_set_thread2.start()
        exchange_rate_set_thread3.start()
        time.sleep(10)

        # Query User A and User B bank balance
        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at start of simple functional test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})
        status, acc2_balance = query_balances(accounts1[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances at start of simple functional test: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

        # User A supplies and collaterlizes 10000 umee
        status = tx_supply(accounts1[0]["name"], "10000000000uumee", validator1_home)
        self.assertTrue(status)

        status = tx_collateralize(accounts1[0]["name"], "10000000000u/uumee", validator1_home)
        self.assertTrue(status)

        # User B supplies 2 atom
        status = tx_supply(accounts1[1]["name"], "2000000ibc/atom", validator1_home)
        self.assertTrue(status)

        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after supplying and collateralizing 10000 umee: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts1[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after supplying 2 atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9998000000','ibc/juno':'20000000000','u/ibc/atom':'2000000','uumee':'1000000000000'})

        # User A borrows 1 atom
        status = tx_borrow(accounts1[0]["name"], "1000000ibc/atom", validator1_home)
        self.assertTrue(status)

        # User B withdraws 1 atom
        status = tx_withdraw(accounts1[1]["name"], "1000000u/ibc/atom", validator1_home)
        self.assertTrue(status)

        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after borrowing 1 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10001000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts1[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after withdrawing 1 u/atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9999000000','ibc/juno':'20000000000','u/ibc/atom':'1000000','uumee':'1000000000000'})

        # User A pays back 1 atom
        status = tx_repay(accounts1[0]["name"], "1000000ibc/atom", validator1_home)
        self.assertTrue(status)

        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances after repaying 1 atom: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        status, acc2_balance = query_balances(accounts1[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances after acc1 repaid 1 atom: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'9999000000','ibc/juno':'20000000000','u/ibc/atom':'1000000','uumee':'1000000000000'})

        # Restore initial balances for User A and User B
        # User A decollateralizes and withdraws 10000 umee
        status = tx_decollateralize(accounts1[0]["name"], "10000000000u/uumee", validator1_home)
        self.assertTrue(status)
        status = tx_withdraw(accounts1[0]["name"], "10000000000u/uumee", validator1_home)
        self.assertTrue(status)

        # User B withdraws 1 atom
        status = tx_withdraw(accounts1[1]["name"], "1000000u/ibc/atom", validator1_home)
        self.assertTrue(status)

        status, acc1_balance = query_balances(accounts1[0]["address"])
        self.assertTrue(status)
        print("\nAcc1 balances at end of simple functional test: ", acc1_balance["balances"])
        self.assert_equal_balances(acc1_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})
        status, acc2_balance = query_balances(accounts1[1]["address"])
        self.assertTrue(status)
        print("\nAcc2 balances at end of simple functional test: ", acc2_balance["balances"])
        self.assert_equal_balances(acc2_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})


        # Stop exhange rate setting thread
        self.stop_exchange_rate_set = True
        exchange_rate_set_thread1.join()
        exchange_rate_set_thread2.join()
        exchange_rate_set_thread3.join()

    GH Issue: https://github.com/umee-network/umee/issues/1207
    Collateral weight and liquidation threshold is set to 0.75 so that borrow limit
    for each account is 150 usd when supply and collateralizing 200 usd. Borrow rates
    are set to 0 to make tracking changing balances simpler
    def test_functional_one(self):
        # Submit exhange rates to price feeder every voting period in the background
        exchange_rate_set_thread1 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator1_val, validator1_home))
        exchange_rate_set_thread2 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator2_val, validator2_home))
        exchange_rate_set_thread3 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator3_val, validator3_home))
        exchange_rate_set_thread1.start()
        exchange_rate_set_thread2.start()
        exchange_rate_set_thread3.start()
        time.sleep(10)

        # account1, ..., account50 supply 10000 umee, account51, ..., account100 supply 1000 umee,
        # account101, ..., account200 supply 10000 atom and 200 juno
        t1 = threading.Thread(target=self.batch_supply, args=(accounts1, 0, 50, "10000000000uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_supply, args=(accounts1, 50, 100, "1000000000uumee", validator1_home))
        t3 = threading.Thread(target=self.batch_supply, args=(accounts1, 100, 200, "1000000000ibc/atom", validator1_home))
        t4 = threading.Thread(target=self.batch_supply, args=(accounts1, 100, 200, "200000000ibc/juno", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        t4.start()
        t4.join()

        time.sleep(10)

        # account1, ..., account50 collateralize 10000 umee, account51, ..., account100 collateralize 1000 umee,
        # account101, ..., account200 collateralize 10000 atom and 200 juno
        t1 = threading.Thread(target=self.batch_collateralize, args=(accounts1, 0, 50, "10000000000u/uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_collateralize, args=(accounts1, 50, 100, "1000000000u/uumee", validator1_home))
        t3 = threading.Thread(target=self.batch_collateralize, args=(accounts1, 100, 200, "1000000000u/ibc/atom", validator1_home))
        t4 = threading.Thread(target=self.batch_collateralize, args=(accounts1, 100, 200, "200000000u/ibc/juno", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        t4.start()
        t4.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,50):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(50,100):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'999000000000'})
        for i in range(100,200):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'9000000000','ibc/juno':'19800000000','uumee':'1000000000000'})

        # Every 1min, 9 times in total, acount51, ..., account100 supply and collateralize 1000 umee
        for _ in range(9):
            self.batch_supply(accounts1, 50, 100, "1000000000uumee", validator1_home)
            self.batch_collateralize(accounts1, 50, 100, "1000000000u/uumee", validator1_home)
            time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,50):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(50,100):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(100,200):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'9000000000','ibc/juno':'19800000000','uumee':'1000000000000'})

        # In parallel, account1, ..., account20 borrow 10 atom, account21, ..., account40 borrow 100 atom,
        # account41, ..., account60 borrow 150 atom, account61, ..., account100 borrow 300 juno
        t1 = threading.Thread(target=self.batch_borrow, args=(accounts1, 0, 20, "10000000ibc/atom", validator1_home))
        t2 = threading.Thread(target=self.batch_borrow, args=(accounts1, 20, 40, "100000000ibc/atom", validator1_home))
        t3 = threading.Thread(target=self.batch_borrow, args=(accounts1, 40, 60, "150000000ibc/atom", validator1_home))
        t4 = threading.Thread(target=self.batch_borrow, args=(accounts1, 60, 100, "300000000ibc/juno", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,20):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10010000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(20,40):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10100000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(40,60):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10150000000','ibc/juno':'20000000000','uumee':'990000000000'})
        for i in range(60,100):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20300000000','uumee':'990000000000'})

        # Stop exhange rate setting thread
        self.stop_exchange_rate_set = True
        exchange_rate_set_thread1.join()
        exchange_rate_set_thread2.join()
        exchange_rate_set_thread3.join()

        # Price of atom grows to 2 usd, price of juno grows to 0.7 usd. Restart exchange rate setting with new rates
        self.stop_exchange_rate_set = False
        exchange_rate_set_thread1 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES, validator1_val, validator1_home))
        exchange_rate_set_thread2 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES, validator2_val, validator2_home))
        exchange_rate_set_thread3 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES, validator3_val, validator3_home))
        exchange_rate_set_thread1.start()
        exchange_rate_set_thread2.start()
        exchange_rate_set_thread3.start()
        time.sleep(20)

        status, targets = query_liquidation_targets()
        self.assertTrue(status)
        self.assertTrue(len(targets['targets']) == 80, "There should be 80 accounts able to be liquidated (i.e. acount21 - acount100)")

        for t in targets['targets']:
            status, summary = query_account_summary(t)
            self.assertTrue(status)
            self.assertTrue(summary['borrowed_value'] > summary['liquidation_threshold'], f'Account with address {t} should not be a liquidation target')

        # Query account summaries before liquidations
        for i in range(0,20):
            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '200.000000000000000000', 'collateral_value': '200.000000000000000000', 'borrowed_value': '20.000000000000000000', 'borrow_limit': '150.000000000000000000', 'liquidation_threshold': '150.000000000000000000'})
        for i in range(20,40):
            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '200.000000000000000000', 'collateral_value': '200.000000000000000000', 'borrowed_value': '200.000000000000000000', 'borrow_limit': '150.000000000000000000', 'liquidation_threshold': '150.000000000000000000'})
        for i in range(40,60):
            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '200.000000000000000000', 'collateral_value': '200.000000000000000000', 'borrowed_value': '300.000000000000000000', 'borrow_limit': '150.000000000000000000', 'liquidation_threshold': '150.000000000000000000'})
        for i in range(60,100):
            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '200.000000000000000000', 'collateral_value': '200.000000000000000000', 'borrowed_value': '210.000000000000000000', 'borrow_limit': '150.000000000000000000', 'liquidation_threshold': '150.000000000000000000'})


        # Liquidate whatever possible in parallel (acount21, ..., acount100)
        max_juno_ammount = 300000000 * (200/210) # Juno amount as 200 usd since that is amount collateralized
        t1 = threading.Thread(target=self.batch_liquidate, args=(liquidators1, accounts1, 20, 40, "100000000ibc/atom", "uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_liquidate, args=(liquidators1, accounts1, 40, 60, "100000000ibc/atom", "uumee", validator1_home))
        t3 = threading.Thread(target=self.batch_liquidate, args=(liquidators1, accounts1, 60, 100, str(max_juno_ammount) + "ibc/juno", "uumee", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly and account summaries after liquidations
        for i in range(0,20):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10010000000','ibc/juno':'20000000000','uumee':'990000000000'})
            self.assert_equal_balances(liq_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '200.000000000000000000', 'collateral_value': '200.000000000000000000', 'borrowed_value': '20.000000000000000000', 'borrow_limit': '150.000000000000000000', 'liquidation_threshold': '150.000000000000000000'})

            
        for i in range(20,40):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10100000000','ibc/juno':'20000000000','uumee':'990000000000'})
            self.assert_equal_balances(liq_balance, {'ibc/atom':'9908256880','ibc/juno':'20000000000','uumee':'1010000000000'})

            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '0.000000000000000000', 'collateral_value': '0.000000000000000000', 'borrowed_value': '16.513760000000000000', 'borrow_limit': '0.000000000000000000', 'liquidation_threshold': '0.000000000000000000'})
            
        for i in range(40,60):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10150000000','ibc/juno':'20000000000','uumee':'990000000000'})
            self.assert_equal_balances(liq_balance, {'ibc/atom':'9908256880','ibc/juno':'20000000000','uumee':'1010000000000'})

            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '0.000000000000000000', 'collateral_value': '0.000000000000000000', 'borrowed_value': '116.513760000000000000', 'borrow_limit': '0.000000000000000000', 'liquidation_threshold': '0.000000000000000000'})
            
        for i in range(60,100):
            status, acc_balance = query_balances(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators1[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20300000000','uumee':'990000000000'})
            self.assert_equal_balances(liq_balance, {'ibc/atom':'10000000000','ibc/juno':'19737876802','uumee':'1009999999999'})

            status, summary = query_account_summary(accounts1[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '0.000000020000000000', 'collateral_value': '0.000000020000000000', 'borrowed_value': '26.513761400000000000', 'borrow_limit': '0.000000015000000000', 'liquidation_threshold': '0.000000015000000000'})

        # Stop exhange rate setting thread
        self.stop_exchange_rate_set = True
        exchange_rate_set_thread1.join()
        exchange_rate_set_thread2.join()
        exchange_rate_set_thread3.join()

    # GH Issue: https://github.com/umee-network/umee/issues/1208
    def test_functional_two(self):
        # Submit exhange rates to price feeder every voting period in the background
        exchange_rate_set_thread1 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator1_val, validator1_home))
        exchange_rate_set_thread2 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator2_val, validator2_home))
        exchange_rate_set_thread3 = threading.Thread(target=self.exchange_rate_set, args=(EXCHANGE_RATES, validator3_val, validator3_home))
        exchange_rate_set_thread1.start()
        exchange_rate_set_thread2.start()
        exchange_rate_set_thread3.start()
        time.sleep(10)

        # account1, ..., account50 supply 10000 umee, account51, ..., account100 supply 1000 umee,
        # account101, ..., account200 supply 10000 atom and 200 juno
        t1 = threading.Thread(target=self.batch_supply, args=(accounts2, 0, 50, "40000000000uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_supply, args=(accounts2, 50, 100, "4000000000uumee", validator1_home))
        t3 = threading.Thread(target=self.batch_supply, args=(accounts2, 100, 200, "1000000000ibc/atom", validator1_home))
        t4 = threading.Thread(target=self.batch_supply, args=(accounts2, 100, 200, "200000000ibc/juno", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        t4.start()
        t4.join()

        time.sleep(10)

        # account1, ..., account50 collateralize 10000 umee, account51, ..., account100 collateralize 1000 umee,
        # account101, ..., account200 collateralize 10000 atom and 200 juno
        t1 = threading.Thread(target=self.batch_collateralize, args=(accounts2, 0, 50, "40000000000u/uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_collateralize, args=(accounts2, 50, 100, "4000000000u/uumee", validator1_home))
        t3 = threading.Thread(target=self.batch_collateralize, args=(accounts2, 100, 200, "1000000000u/ibc/atom", validator1_home))
        t4 = threading.Thread(target=self.batch_collateralize, args=(accounts2, 100, 200, "200000000u/ibc/juno", validator1_home))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        t4.start()
        t4.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,50):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(50,100):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'996000000000'})
        for i in range(100,200):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'9000000000','ibc/juno':'19800000000','uumee':'1000000000000'})

        # Every 1min, 9 times in total, acount51, ..., account100 supply and collateralize 1000 umee
        for _ in range(9):
            self.batch_supply(accounts2, 50, 100, "4000000000uumee", validator1_home)
            self.batch_collateralize(accounts2, 50, 100, "4000000000u/uumee", validator1_home)
            time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,50):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(50,100):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(100,200):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'9000000000','ibc/juno':'19800000000','uumee':'1000000000000'})

        # In parallel, account1, ..., account20 borrow 10 atom, account21, ..., account40 borrow 100 atom,
        # account41, ..., account60 borrow 150 atom, account61, ..., account100 borrow 300 juno, 
        # account101, ..., account200 borrow 35000 umee
        # t1 = threading.Thread(target=self.batch_borrow, args=(accounts2, 0, 20, "10000000ibc/atom", validator1_home))
        # t2 = threading.Thread(target=self.batch_borrow, args=(accounts2, 20, 40, "100000000ibc/atom", validator1_home))
        # t3 = threading.Thread(target=self.batch_borrow, args=(accounts2, 40, 60, "150000000ibc/atom", validator1_home))
        # t4 = threading.Thread(target=self.batch_borrow, args=(accounts2, 60, 100, "300000000ibc/juno", validator1_home))
        t5 = threading.Thread(target=self.batch_borrow, args=(accounts2, 100, 200, "35000000000uumee", validator1_home))
        # t1.start()
        # t2.start()
        # t3.start()
        # t4.start()
        t5.start()
        # t1.join()
        # t2.join()
        # t3.join()
        # t4.join()
        t5.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly
        for i in range(0,20):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(20,40):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(40,60):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(60,100):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'960000000000'})
        for i in range(100,200):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            self.assert_equal_balances(acc_balance, {'ibc/atom':'9000000000','ibc/juno':'19800000000','uumee':'1035000000000'})

        # Stop exhange rate setting thread
        self.stop_exchange_rate_set = True
        exchange_rate_set_thread1.join()
        exchange_rate_set_thread2.join()
        exchange_rate_set_thread3.join()

        # Price of umee grows to 0.04 usd. Restart exchange rate setting with new rates
        self.stop_exchange_rate_set = False
        exchange_rate_set_thread1 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES2, validator1_val, validator1_home))
        exchange_rate_set_thread2 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES2, validator2_val, validator2_home))
        exchange_rate_set_thread3 = threading.Thread(target=self.exchange_rate_set, args=(UPDATED_EXCHANGE_RATES2, validator3_val, validator3_home))
        exchange_rate_set_thread1.start()
        exchange_rate_set_thread2.start()
        exchange_rate_set_thread3.start()
        time.sleep(20)

        status, targets = query_liquidation_targets()
        self.assertTrue(status)
        self.assertTrue(len(targets['targets']) == 100, "There should be 100 accounts able to be liquidated (i.e. acount101 - acount200)")

        for t in targets['targets']:
            status, summary = query_account_summary(t)
            self.assertTrue(status)
            self.assertTrue(summary['borrowed_value'] > summary['liquidation_threshold'], f'Account with address {t} should not be a liquidation target')

        # Query account summaries before liquidations
        for i in range(0,20):
            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '1600.000000000000000000', 'collateral_value': '1600.000000000000000000', 'borrowed_value': '0.000000000000000000', 'borrow_limit': '1200.000000000000000000', 'liquidation_threshold': '1200.000000000000000000'})
        for i in range(20,40):
            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '1600.000000000000000000', 'collateral_value': '1600.000000000000000000', 'borrowed_value': '0.000000000000000000', 'borrow_limit': '1200.000000000000000000', 'liquidation_threshold': '1200.000000000000000000'})
        for i in range(40,60):
            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '1600.000000000000000000', 'collateral_value': '1600.000000000000000000', 'borrowed_value': '0.000000000000000000', 'borrow_limit': '1200.000000000000000000', 'liquidation_threshold': '1200.000000000000000000'})
        for i in range(60,100):
            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '1600.000000000000000000', 'collateral_value': '1600.000000000000000000', 'borrowed_value': '0.000000000000000000', 'borrow_limit': '1200.000000000000000000', 'liquidation_threshold': '1200.000000000000000000'})
        for i in range(100,200):
            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} before liquidations: {summary}')
            self.assert_equal_summaries(summary, {'supplied_value': '1100.000000000000000000', 'collateral_value': '1100.000000000000000000', 'borrowed_value': '1400.000000000000000000', 'borrow_limit': '825.000000000000000000', 'liquidation_threshold': '825.000000000000000000'})


        # Liquidate whatever possible in parallel (acount101, ..., acount200)
        t1 = threading.Thread(target=self.batch_liquidate, args=(liquidators2, accounts2, 100, 200, "1000000000ibc/atom", "uumee", validator1_home))
        t2 = threading.Thread(target=self.batch_liquidate, args=(liquidators2, accounts2, 100, 200, "200000000ibc/juno", "uumee", validator1_home))
        t1.start()
        t1.join()
        t2.start()
        t2.join()

        time.sleep(10)

        # Query account balances to make sure transactions went through correctly and account summaries after liquidations
        for i in range(0,20):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            # self.assert_equal_balances(acc_balance, {'ibc/atom':'10010000000','ibc/juno':'20000000000','uumee':'990000000000'})
            # self.assert_equal_balances(liq_balance, {'ibc/atom':'10000000000','ibc/juno':'20000000000','uumee':'1000000000000'})

            status, summary = query_account_summary(accounts2[i]["address"])
            # self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            # self.assert_equal_summaries(summary, {'supplied_value': '400.000000000000000000', 'collateral_value': '400.000000000000000000', 'borrowed_value': '10.000000000000000000', 'borrow_limit': '300.000000000000000000', 'liquidation_threshold': '300.000000000000000000'})

            
        for i in range(20,40):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            # self.assert_equal_balances(acc_balance, {'ibc/atom':'10100000000','ibc/juno':'20000000000','uumee':'990000000000'})
            # self.assert_equal_balances(liq_balance, {'ibc/atom':'9908256880','ibc/juno':'20000000000','uumee':'1010000000000'})

            status, summary = query_account_summary(accounts2[i]["address"])
            # self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            # self.assert_equal_summaries(summary, {'supplied_value': '400.000000000000000000', 'collateral_value': '400.000000000000000000', 'borrowed_value': '100.000000000000000000', 'borrow_limit': '300.000000000000000000', 'liquidation_threshold': '300.000000000000000000'})
            
        for i in range(40,60):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            # self.assert_equal_balances(acc_balance, {'ibc/atom':'10150000000','ibc/juno':'20000000000','uumee':'990000000000'})
            # self.assert_equal_balances(liq_balance, {'ibc/atom':'9908256880','ibc/juno':'20000000000','uumee':'1010000000000'})

            status, summary = query_account_summary(accounts2[i]["address"])
            # self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            # self.assert_equal_summaries(summary, {'supplied_value': '400.000000000000000000', 'collateral_value': '400.000000000000000000', 'borrowed_value': '150.000000000000000000', 'borrow_limit': '300.000000000000000000', 'liquidation_threshold': '300.000000000000000000'})
            
        for i in range(60,100):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            # self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20300000000','uumee':'990000000000'})
            # self.assert_equal_balances(liq_balance, {'ibc/atom':'10000000000','ibc/juno':'19737876802','uumee':'1009999999999'})

            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            # self.assert_equal_summaries(summary, {'supplied_value': '400.000000000000000000', 'collateral_value': '400.000000000000000000', 'borrowed_value': '200.000000000000000000', 'borrow_limit': '300.000000000000000000', 'liquidation_threshold': '300.000000000000000000'})

        for i in range(100,200):
            status, acc_balance = query_balances(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for account{i+1}: {acc_balance}')
            status, liq_balance = query_balances(liquidators2[i]["address"])
            self.assertTrue(status)
            print(f'Acc_balance for liquidator{i+1}: {liq_balance}')
            # self.assert_equal_balances(acc_balance, {'ibc/atom':'10000000000','ibc/juno':'20300000000','uumee':'990000000000'})
            # self.assert_equal_balances(liq_balance, {'ibc/atom':'10000000000','ibc/juno':'19737876802','uumee':'1009999999999'})

            status, summary = query_account_summary(accounts2[i]["address"])
            self.assertTrue(status)
            print(f'Account summary for account{i+1} after liquidations: {summary}')
            # self.assert_equal_summaries(summary, {'supplied_value': '1100.000000000000000000', 'collateral_value': '1100.000000000000000000', 'borrowed_value': '1600.000000000000000000', 'borrow_limit': '825.000000000000000000', 'liquidation_threshold': '825.000000000000000000'})

        # Stop exhange rate setting thread
        self.stop_exchange_rate_set = True
        exchange_rate_set_thread1.join()
        exchange_rate_set_thread2.join()
        exchange_rate_set_thread3.join()

if __name__ == "__main__":
    logging.info("INFO: running leverage module tests")
    test_src = inspect.getsource(TestLeverageModuleTxsQueries)
    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
        test_src.index(f"def {x}") - test_src.index(f"def {y}")
    )
    unittest.main(verbosity=2)
