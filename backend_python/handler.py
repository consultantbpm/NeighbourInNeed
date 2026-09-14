import json
from dispatcher import run_dispatcher
from meds import run_meds_check

def lambda_handler(event, context):
    """
    AWS Lambda Handler care rutează cererile către agenți
    pe baza endpoint-urilor definite.
    """
    path = event.get("rawPath", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    
    # Aici s-ar face validarea token-ului Firebase din antetul Authorization
    
    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        body = {}
        
    if method == "POST":
        if path == "/sos":
            response = run_dispatcher(body)
            return {"statusCode": 200, "body": json.dumps(response)}
            
        elif path.startswith("/sos/") and path.endswith("/answer"):
            # Răspuns de la verificarea sos
            return {"statusCode": 200, "body": json.dumps({"decision": "verify", "speak": "Am înțeles."})}
            
        elif path == "/meds/check":
            response = run_meds_check(body)
            return {"statusCode": 200, "body": json.dumps(response)}
            
        elif path == "/meds/prescription":
            return {"statusCode": 200, "body": json.dumps({"meds": [], "speak": "Rețetă analizată"})}
            
        elif path == "/hazard":
            return {"statusCode": 200, "body": json.dumps({"ticketId": "haz_1", "severity": "info"})}
            
        elif path == "/request":
            return {"statusCode": 200, "body": json.dumps({"ticketId": "req_1", "candidates": [], "speak": "Cerere trimisă"})}
            
    return {"statusCode": 404, "body": json.dumps({"error": "Not Found"})}
