import unittest

from rd_theory import RDTheory


class TestRDTheory(unittest.TestCase):
    def test_ias_blocks_below_reserve(self):
        system = RDTheory(alphabet=100.0, reserve_limit=10.0)
        allowed = system.attempt_Z(95)
        self.assertFalse(allowed)
        self.assertEqual(system.alphabet, 100.0)

    def test_progress_and_knowledge_drop(self):
        system = RDTheory(alphabet=100.0, reserve_limit=10.0)
        allowed = system.attempt_Z(10)
        self.assertTrue(allowed)
        self.assertLess(system.alphabet, 100.0)
        self.assertLess(system.knowledge_threads, 100.0)

    def test_forgetting_principle_is_triggered(self):
        system = RDTheory(alphabet=100.0, reserve_limit=10.0)
        # A larger burn eventually destroys enough of A-Y to trigger the forgetting signal.
        system.attempt_Z(25)
        self.assertLess(system.knowledge_threads, 100.0)


if __name__ == "__main__":
    unittest.main()
