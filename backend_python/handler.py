import json
from dispatcher import run_dispatcher
from meds import run_meds_check


def _json_response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "body": json.dumps(body)}


def lambda_handler(event, context):
    """
    AWS Lambda Handler care rutează cererile către agenți pe baza endpoint-urilor definite.

    Contract de răspuns, pentru toate rutele: JSON cu cel puțin cheia "ok" (bool). 200 pentru
    succes, 400 pentru payload invalid, 404 pentru rută necunoscută, 500 pentru erori
    neprevăzute (prinse aici, niciodată propagate necaptate spre apelant).
    """
    path = event.get("rawPath", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")

    # Aici s-ar face validarea token-ului Firebase din antetul Authorization

    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        return _json_response(400, {"ok": False, "motiv": "body JSON invalid"})

    if not isinstance(body, dict):
        return _json_response(400, {"ok": False, "motiv": "body trebuie să fie un obiect JSON"})

    if method == "POST":
        try:
            if path == "/sos":
                response = run_dispatcher(body)
                status = 200 if response.get("ok") else 400
                return _json_response(status, response)

            elif path.startswith("/sos/") and path.endswith("/answer"):
                # Răspuns de la verificarea sos
                return _json_response(200, {"ok": True, "decision": "verify", "speak": "Am înțeles."})

            elif path == "/meds/check":
                response = run_meds_check(body)
                status = 200 if response.get("ok") else 400
                return _json_response(status, response)

            elif path == "/meds/prescription":
                return _json_response(200, {"ok": True, "meds": [], "speak": "Rețetă analizată"})

            elif path == "/hazard":
                return _json_response(200, {"ok": True, "ticketId": "haz_1", "severity": "info"})

            elif path == "/request":
                return _json_response(200, {"ok": True, "ticketId": "req_1", "candidates": [], "speak": "Cerere trimisă"})
        except Exception as e:
            # Nicio excepție neprevăzută nu iese necaptată din handler — demo-ul trebuie să
            # primească mereu un JSON valid, chiar dacă e un 500.
            return _json_response(500, {"ok": False, "motiv": f"eroare internă: {e}"})

    return _json_response(404, {"ok": False, "motiv": "not found"})
