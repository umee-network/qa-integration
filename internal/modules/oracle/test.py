import time
import logging
import unittest
import inspect
import pathlib
from internal.modules.gov.tx import submit_and_pass_proposal
from internal.modules.oracle.query import (
    query_aggregate_prevote,
    query_aggregate_vote,
    node_status,
)
from utils import env
from internal.core.keys import keys_show

from modules.oracle.query import (
    query_feeder_delegation,
    query_params,
)

from modules.oracle.tx import (
    tx_submit_prevote,
    tx_submit_vote,
    tx_delegate_feed_consent,
)

from modules.oracle.hash import (
    get_hash,
)

from modules.oracle.rates import (
    ExchangeRates,
    ExchangeRate
)

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

EXCHANGE_RATES = ExchangeRates(
    ExchangeRate("UMEE", "0.02"),
    ExchangeRate("ATOM", "1.00"),
    ExchangeRate("JUNO", "0.50"),
)

BLOCKS_PER_VOTING_PERIOD = 5
STATIC_SALT = "af8ed1e1f34ac1ac00014581cbc31f2f24480b09786ac83aabf2765dada87509"

validator1_home = f"{env.DAEMON_HOME}-1"
validator2_home = f"{env.DAEMON_HOME}-2"
validator3_home = f"{env.DAEMON_HOME}-3"

validator1_val = keys_show("validator1", "val")[1]
validator2_val = keys_show("validator2", "val", validator2_home)[1]
validator3_val = keys_show("validator3", "val", validator3_home)[1]

def get_block_height():
    _, message = node_status()
    return message["SyncInfo"]["latest_block_height"]

def wait_for_next_voting_period():
    block_height = int(get_block_height())
    vp_block_height = (block_height % BLOCKS_PER_VOTING_PERIOD)
    if vp_block_height > 0:
        time.sleep((BLOCKS_PER_VOTING_PERIOD - vp_block_height) / 2)

class TestOracleModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        update_params = pathlib.Path().resolve().joinpath("./internal/modules/oracle/update-params.json")
        submit_and_pass_proposal(
            proposal_file_or_name=update_params,
            proposal_type='param-change'
        )
        time.sleep(20) # Wait for gov proposal to pass

    def test_query_oracle_params(self):
        status, res = query_params()
        self.assertTrue(status)
        self.assertEqual(len(res['params']['accept_list']), 3)

    # test_prevotes tests to make sure that we can submit prevotes
    def test_prevotes(self):
        # Get Hash
        vote_hash_1 = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator1_val["address"])
        vote_hash_2 = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator2_val["address"])

        wait_for_next_voting_period()

        # Submit 1st prevote
        status, prevote_1 = tx_submit_prevote(validator1_val["name"], vote_hash_1, validator1_home)
        self.assertTrue(status)

        # Query to verify 1st prevote exists
        status, prevote_1 = query_aggregate_prevote(validator1_val["address"])
        self.assertTrue(status)
        self.assertEqual(prevote_1["aggregate_prevote"]["hash"].upper(), vote_hash_1)

        wait_for_next_voting_period()

        # # Submit 2nd prevote
        status, prevote_2 = tx_submit_prevote(validator2_val["name"], vote_hash_2, validator2_home)
        self.assertTrue(status)

        # Query to verify 2nd prevote exists
        status, prevote_2 = query_aggregate_prevote(validator2_val["address"])
        self.assertTrue(status)
        self.assertEqual(prevote_2["aggregate_prevote"]["hash"].upper(), vote_hash_2)

    # TODO - test to verify no aggregate pre-vote error (the vote happens more than one VP later or in same VP)

    # test_votes tests to make sure that we can submit votes
    def test_votes(self):
        # Get Hash
        vote_hash = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator3_val["address"])

        wait_for_next_voting_period()

        # Submit prevote
        status, prevote_1 = tx_submit_prevote(validator3_val["name"], vote_hash, validator3_home)
        self.assertTrue(status)

        time.sleep(1.5) # Wait until next voting period

        # Submit vote
        status, vote_1 = tx_submit_vote(validator3_val["name"], STATIC_SALT, validator3_home, EXCHANGE_RATES.ToString())
        self.assertTrue(status)

        # Query votes to make sure they exist, and are correct
        status, vote_1 = query_aggregate_vote(validator3_val["address"])
        self.assertTrue(status)

        self.assertEqual(len(vote_1["aggregate_vote"]["exchange_rate_tuples"]), EXCHANGE_RATES.Len())

        for rate in vote_1["aggregate_vote"]["exchange_rate_tuples"]:
            self.assertEqual(float(rate["exchange_rate"]), float(EXCHANGE_RATES.GetRate(rate["denom"])))

    # Test delegating feed consent from operator to delegate,
    # then submit voting from delegate on behalf of operator
    def test_delegate_feed_consent(self):
        operator_name = validator1_val["name"]
        operator_val_address = validator1_val["address"]
        operator_home = validator1_home

        # Using a non-validator account
        sender = keys_show("account2")[1]
        delegate_name = sender["name"]
        delegate_home = validator1_home
        delegate_acc_address = sender["address"]

        status, response = tx_delegate_feed_consent(operator_name, delegate_acc_address, operator_home)
        self.assertTrue(status)

        # Test query route and verify feeder is delegated correctly
        status, response = query_feeder_delegation(operator_val_address)
        self.assertTrue(status)
        self.assertEqual(delegate_acc_address, response["feeder_addr"])

        vote_hash = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, operator_val_address)

        wait_for_next_voting_period()

        status = tx_submit_prevote(delegate_name, vote_hash, delegate_home, operator_val_address)
        self.assertTrue(status)

        status, response = query_aggregate_prevote(operator_val_address)
        self.assertTrue(status)

        time.sleep(1.5) # Wait until next voting period

        status = tx_submit_vote(
            delegate_name, 
            STATIC_SALT, 
            validator1_home, 
            EXCHANGE_RATES.ToString(),  
            operator_val_address
        )
        self.assertTrue(status)

        status = query_aggregate_vote(validator1_val["address"])
        self.assertTrue(status)

    # test_hash makes sure our hasher is accurate
    def test_hash(self):
        hash = get_hash("ATOM:11.1,USDT:1.00001", "salt", "umeevaloper1zypqa76je7pxsdwkfah6mu9a583sju6xjettez")
        self.assertEqual(hash, "D1C46537806D87B71827065BF0AF35647936D556")

if __name__ == "__main__":
    logging.info("INFO: running oracle module tests")
    test_src = inspect.getsource(TestOracleModule)
    unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: (
        test_src.index(f"def {x}") - test_src.index(f"def {y}")
    )
    unittest.main(verbosity=2)
