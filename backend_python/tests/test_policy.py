import unittest
from dispatcher import run_dispatcher
from meds import run_meds_check

class TestPolicy(unittest.TestCase):
    def test_sos_button(self):
        payload = {"group_id": "g1", "uid": "u1", "source": "watch_button", "lat": 44.4, "lng": 26.1}
        res = run_dispatcher(payload)
        self.assertTrue(res["ok"])
        self.assertIsNotNone(res["ticket_id"])
        self.assertIsNotNone(res["responder"])

    def test_meds_check(self):
        payload = {"uid": "u1", "groupId": "g1", "imageBase64": "dummy"}
        res = run_meds_check(payload)
        self.assertTrue(res["ok"])
        self.assertTrue(res["matchesProfile"])
        self.assertIn("speak", res)

if __name__ == "__main__":
    unittest.main()
