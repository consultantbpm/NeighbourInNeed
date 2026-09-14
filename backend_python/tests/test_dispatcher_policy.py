import unittest

import dispatcher
from dispatcher import select_responder, validate_sos_payload, PayloadValidationError, run_dispatcher


class TestSelectResponder(unittest.TestCase):
    """Selecția responder-ului trebuie să fie determinist: (1) cazul simplu — cel mai
    apropiat; (2) cu abilitate cerută explicit; (3) fără niciun membru disponibil."""

    def test_alege_cel_mai_apropiat(self):
        members = [
            {"uid": "a", "distance": 500, "skills": []},
            {"uid": "b", "distance": 100, "skills": []},
        ]
        self.assertEqual(select_responder(members)["uid"], "b")

    def test_prioritizeaza_skill_cerut_peste_distanta(self):
        members = [
            {"uid": "a", "distance": 50, "skills": []},
            {"uid": "b", "distance": 300, "skills": ["nurse"]},
        ]
        self.assertEqual(select_responder(members, required_skill="nurse")["uid"], "b")

    def test_niciun_membru_disponibil_acum(self):
        members = [{"uid": "a", "distance": 50, "available": False}]
        self.assertIsNone(select_responder(members))


class TestValidateSosPayload(unittest.TestCase):
    """Validarea payload-ului: (1) payload valid nu ridică; (2) câmp obligatoriu lipsă
    ridică PayloadValidationError cu mesaj clar."""

    def test_payload_valid_nu_ridica(self):
        payload = {"group_id": "g1", "uid": "u1", "lat": 44.4, "lng": 26.1}
        validate_sos_payload(payload)  # nu ridică excepție

    def test_lipsa_group_id_ridica_eroare_clara(self):
        payload = {"uid": "u1", "lat": 44.4, "lng": 26.1}
        with self.assertRaises(PayloadValidationError) as ctx:
            validate_sos_payload(payload)
        self.assertIn("group_id", str(ctx.exception))


class TestFallbackFaraMembri(unittest.TestCase):
    """Dacă get_nearby_members nu întoarce niciun membru, run_dispatcher trebuie să
    notifice tot grupul și să marcheze tichetul 'neacoperit', nu să pice."""

    def test_niciun_membru_notifica_grupul_si_marcheaza_neacoperit(self):
        original = dispatcher.get_nearby_members
        dispatcher.get_nearby_members = lambda *args, **kwargs: []
        try:
            payload = {"group_id": "g1", "uid": "u1", "source": "watch_button", "lat": 44.4, "lng": 26.1}
            res = run_dispatcher(payload)
            self.assertTrue(res["ok"])
            self.assertIsNone(res["responder"])
            self.assertIn("niciun membru", res["motiv"])
            pasi = [entry["pas"] for entry in res["istoric"]]
            self.assertIn("fallback", pasi)
        finally:
            dispatcher.get_nearby_members = original


if __name__ == "__main__":
    unittest.main()
