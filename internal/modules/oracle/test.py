import time
import logging
import unittest
import json
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
    query_params,
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
    ExchangeRate
)

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

EXCHANGE_RATES = ExchangeRates(
    ExchangeRate("UMEE", "0.02"),
    ExchangeRate("ATOM", "1.00"),
    ExchangeRate("JUNO", "0.50"),
)

STATIC_SALT = "af8ed1e1f34ac1ac00014581cbc31f2f24480b09786ac83aabf2765dada87509"

validator1_home = f"{env.DAEMON_HOME}-1"
validator2_home = f"{env.DAEMON_HOME}-2"
validator3_home = f"{env.DAEMON_HOME}-3"

validator1_acc = keys_show("validator1", "val")[1]
validator2_acc = keys_show("validator2", "val", validator2_home)[1]
validator3_acc = keys_show("validator3", "val", validator3_home)[1]

def get_block_height():
    status, message = node_status()
    # TODO - this status is broken and returns false when successful
    return json.loads(message)["SyncInfo"]["latest_block_height"]

class TestOracleModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        update_params = pathlib.Path().resolve().joinpath("./internal/modules/oracle/update-params.json")
        submit_and_pass_proposal(
            proposal_file_or_name=update_params,
            proposal_type='param-change'
        )

    def test_query_oracle_params(self):
        status, res = query_params()
        self.assertTrue(status)
        self.assertTrue(len(res['params']['accept_list']) >= 1, "It should have at least one token in the accept list")

    # test_prevotes tests to make sure that we can submit prevotes
    def test_prevotes(self):
        # Get Hash
        vote_hash_1 = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator1_acc["address"])
        vote_hash_2 = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator2_acc["address"])
        # Submit 1st prevote
        status = tx_submit_prevote(validator1_acc["name"], vote_hash_1, validator1_home)
        self.assertTrue(status)

        # Submit 2nd prevote
        status = tx_submit_prevote(validator2_acc["name"], vote_hash_2, validator2_home)
        self.assertTrue(status)

        # Query to verify prevotes exist
        status, prevote_1 = query_aggregate_prevote(validator1_acc["address"])
        self.assertTrue(status)
        self.assertEqual(prevote_1["aggregate_prevote"]["hash"].upper(), vote_hash_1)
        status, prevote_2 = query_aggregate_prevote(validator2_acc["address"])
        self.assertTrue(status)
        self.assertEqual(prevote_2["aggregate_prevote"]["hash"].upper(), vote_hash_2)

    # test_votes tests to make sure that we can submit votes
    def test_votes(self):
        # Get Hash
        vote_hash = get_hash(EXCHANGE_RATES.ToString(), STATIC_SALT, validator3_acc["address"])

        # Make sure we are not at the last two blocks of a voting period
        block_height = int(get_block_height())
        vp_block_height = (block_height % 5) + 1
        if vp_block_height == 3:
            time.sleep(2)
        if vp_block_height == 4:
            time.sleep(1)

        # Submit prevote
        tx_submit_prevote(validator3_acc["name"], vote_hash, validator3_home)

        # Query prevote
        status, prevote = query_aggregate_prevote(validator3_acc["address"])
        self.assertTrue(status)

        time.sleep(1)

        # Submit vote
        status = tx_submit_vote(validator3_acc["name"], STATIC_SALT, validator3_home, EXCHANGE_RATES.ToString())
        self.assertTrue(status)

        # Query votes to make sure they exist, and are correct
        status, vote_1 = query_aggregate_vote(validator3_acc["address"])
        self.assertTrue(status)
 
        # TODO - fix this assert (only the umee price is currently returned)
        #self.assertEqual(len(vote_1["aggregate_vote"]["exchange_rate_tuples"]), EXCHANGE_RATES.Len)

        for rate in vote_1["aggregate_vote"]["exchange_rate_tuples"]:
            self.assertEqual(float(rate["exchange_rate"]), float(EXCHANGE_RATES.GetRate(rate["denom"])))

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
