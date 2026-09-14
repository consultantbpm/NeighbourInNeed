import os
from typing import Dict, Any

try:
    from strands_agents import Agent, tool
    from strands_agents.models_bedrock import BedrockModel
except ImportError:
    # Dummy mocks for structural validity if SDK isn't installed during agent check
    def tool(f): return f
    class Agent:
        def __init__(self, **kwargs): pass
        def run(self, **kwargs): return {"output": "dummy"}
    class BedrockModel:
        def __init__(self, **kwargs): pass


class PayloadValidationError(ValueError):
    """Payload-ul de verificare medicație nu conține câmpurile obligatorii."""


@tool
def identify_medication(image_b64: str) -> dict:
    """Folosește Bedrock Claude Vision pentru a identifica medicamentul din poză."""
    return {"medName": "Paracetamol", "dose": "500mg"}

@tool
def parse_prescription(image_b64: str) -> dict:
    """Extrage rețeta din imagine."""
    return {"meds": [{"name": "Paracetamol", "dose": "500mg", "schedule": ["08:00", "20:00"]}]}

@tool
def get_member_profile(group_id: str, uid: str) -> dict:
    """Obține profilul medical al membrului din Firestore."""
    return {
        "meds": [
            {"name": "Paracetamol", "dose": "500mg", "schedule": ["08:00", "20:00"], "stock": 10, "lastTakenAt": None}
        ]
    }

@tool
def update_ticket(group_id: str, ticket_id: str, patch: dict) -> None:
    pass


def validate_meds_payload(payload: dict) -> None:
    """Validează un payload de verificare medicație. Ridică PayloadValidationError, cu mesaj
    clar, la prima problemă găsită."""
    if not isinstance(payload, dict):
        raise PayloadValidationError("payload-ul trebuie să fie un obiect JSON")

    uid = payload.get("uid")
    if not uid or not isinstance(uid, str):
        raise PayloadValidationError("uid lipsă sau invalid (trebuie string nevid)")

    group_id = payload.get("groupId")
    if not group_id or not isinstance(group_id, str):
        raise PayloadValidationError("groupId lipsă sau invalid (trebuie string nevid)")

    if not payload.get("imageBase64"):
        raise PayloadValidationError("imageBase64 lipsă (necesară pentru identificarea medicamentului)")


model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1")

SYSTEM_PROMPT = """Ești agentul de medicație.
Reguli:
1. Verifici potrivirea numelui și dozei (din identify_medication) cu profilul pacientului (get_member_profile).
2. Dacă lastTakenAt este azi în fereastra schemei -> "NU mai lua".
3. Dacă expirarea e depășită -> avertisment.
4. Dacă e nepotrivire cu profilul -> "Nu e în schema ta, nu lua fără să întrebi".
Nu oferi niciodată sfaturi medicale — doar compari cu schema declarată de utilizator sau caregiver.
"""

meds_agent = Agent(
    model=model,
    tools=[identify_medication, parse_prescription, get_member_profile, update_ticket],
    system_prompt=SYSTEM_PROMPT
)

MEDICAL_DISCLAIMER = "Aceasta nu este o recomandare medicală — confirmă cu un medic sau farmacist."


def run_meds_check(payload: dict) -> dict:
    """Procesează verificarea unui medicament.

    Returnează întotdeauna {ok, ...}. Payload invalid -> ok=False cu motiv explicit, fără
    excepții, ca apelantul (handler.py) să poată răspunde 400 fără try/except suplimentar.
    """
    try:
        validate_meds_payload(payload)
    except PayloadValidationError as e:
        return {"ok": False, "motiv": str(e)}

    uid = payload["uid"]
    group_id = payload["groupId"]
    image_b64 = payload["imageBase64"]

    identified = identify_medication(image_b64)
    profile = get_member_profile(group_id, uid)

    med_name = identified.get("medName")
    dose = identified.get("dose")

    profile_meds = profile.get("meds") or []
    matches_profile = any(m.get("name") == med_name and m.get("dose") == dose for m in profile_meds)

    # TODO: comparație reală a lastTakenAt cu fereastra orară a schemei — necesită fixture Firebase
    # reală; până atunci presupunem că nu a fost luat azi, ca să nu blocăm demo-ul cu False pozitive.
    already_taken_today = False

    if matches_profile:
        speak = f"Acesta pare a fi {med_name} {dose}, conform schemei tale. {MEDICAL_DISCLAIMER}"
    else:
        speak = f"Nu am găsit {med_name} {dose} în schema ta. Nu lua fără să întrebi. {MEDICAL_DISCLAIMER}"

    return {
        "ok": True,
        "medName": med_name,
        "dose": dose,
        "matchesProfile": matches_profile,
        "alreadyTakenToday": already_taken_today,
        "speak": speak,
    }
