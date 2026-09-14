import unittest
from dispatcher import run_dispatcher
from meds import run_meds_check

class TestPolicy(unittest.TestCase):
    def test_sos_button(self):
        payload = {"groupId": "g1", "uid": "u1", "source": "watch_button"}
        res = run_dispatcher(payload)
        self.assertEqual(res["decision"], "verify")

    def test_meds_check(self):
        payload = {"uid": "u1", "groupId": "g1", "imageBase64": "dummy"}
        res = run_meds_check(payload)
        self.assertTrue(res["matchesProfile"])
        
if __name__ == "__main__":
    unittest.main()
