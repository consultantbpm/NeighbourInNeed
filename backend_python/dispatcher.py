import time
from typing import List, Dict, Any, Optional

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
    """Payload-ul de SOS nu conține câmpurile obligatorii sau are valori invalide."""


@tool
def get_nearby_members(group_id: str, lat: float, lng: float, radius_m: int = 800, available_now: bool = True) -> list:
    """Găsește membrii disponibili din apropiere (din Firebase)."""
    # TODO: Implementare Firebase reală
    return [{"uid": "user123", "distance": 100, "hasCar": True, "skills": ["nurse"]}]

@tool
def create_ticket(group_id: str, payload: dict) -> str:
    """Creează un tichet în Firestore."""
    return "ticket_123"

@tool
def update_ticket(group_id: str, ticket_id: str, patch: dict) -> None:
    """Actualizează un tichet în Firestore."""
    pass

@tool
def notify_group(group_id: str, ticket_id: str, action: str) -> None:
    """Trimite notificare FCM pe topicul grupului."""
    pass

@tool
def notify_member(uid: str, title: str, body: str) -> None:
    """Trimite notificare FCM directă unui membru."""
    pass

@tool
def speak_to_user(uid: str, text: str) -> None:
    """Trimite text TTS spre telefon/ceas."""
    pass

@tool
def call_emergency(uid: str, number: str = "112") -> None:
    """Apelează numărul de urgență."""
    pass

@tool
def find_recent_tickets(group_id: str, type: str, minutes: int = 30) -> list:
    """Găsește tichete recente pentru dedup."""
    return []


def validate_sos_payload(payload: dict) -> None:
    """Validează un payload de SOS. Ridică PayloadValidationError, cu mesaj clar, la prima
    problemă găsită. Nu modifică payload-ul.

    Contract de sârmă (fixat de director, comun cu aplicația Kotlin telefon/ceas):
    POST /sos {"source": "watch_button"|"phone_button"|"phone_sms_fallback", "group_id": str,
    "uid": str, "lat": float, "lng": float, "text": str opțional, "ts": ISO8601 opțional}.
    """
    if not isinstance(payload, dict):
        raise PayloadValidationError("payload-ul trebuie să fie un obiect JSON")

    group_id = payload.get("group_id")
    if not group_id or not isinstance(group_id, str):
        raise PayloadValidationError("group_id lipsă sau invalid (trebuie string nevid)")

    uid = payload.get("uid")
    if not uid or not isinstance(uid, str):
        raise PayloadValidationError("uid lipsă sau invalid (trebuie string nevid)")

    source = payload.get("source")
    valid_sources = {"watch_button", "phone_button", "phone_sms_fallback"}
    if source is not None and source not in valid_sources:
        raise PayloadValidationError(f"source invalid: {source!r} (trebuie unul din {sorted(valid_sources)})")

    lat = payload.get("lat")
    lng = payload.get("lng")
    for name, value in (("lat", lat), ("lng", lng)):
        if value is None:
            raise PayloadValidationError(f"{name} lipsă (obligatoriu pentru a găsi membri din apropiere)")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise PayloadValidationError(f"{name} trebuie să fie număr, primit: {value!r}")
    if not (-90 <= lat <= 90):
        raise PayloadValidationError(f"lat în afara intervalului [-90, 90]: {lat}")
    if not (-180 <= lng <= 180):
        raise PayloadValidationError(f"lng în afara intervalului [-180, 180]: {lng}")


def select_responder(members: List[Dict[str, Any]], required_skill: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Alege responder-ul dintre membrii disponibili, determinist și pur (fără efecte secundare).

    Ordinea criteriilor: (1) are abilitatea cerută, dacă a fost cerută una; (2) distanță
    crescătoare; (3) cele mai multe abilități; (4) uid alfabetic, ca tie-break stabil.
    Returnează None dacă lista e goală sau nimeni nu e disponibil acum.
    """
    candidates = [m for m in members if m.get("available", True)]
    if not candidates:
        return None

    def sort_key(m: Dict[str, Any]):
        distance = m.get("distance", float("inf"))
        skills = m.get("skills") or []
        has_required_skill = 0 if (required_skill and required_skill in skills) else 1
        return (has_required_skill, distance, -len(skills), m.get("uid", ""))

    return sorted(candidates, key=sort_key)[0]


def _log_step(istoric: List[Dict[str, Any]], step: str, detail: Any = "") -> None:
    istoric.append({"pas": step, "detaliu": detail, "timestamp": time.time()})


# Configurarea modelului
# Presupunem us-east-1 pentru Bedrock Claude 3.5 Sonnet
model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1")

SYSTEM_PROMPT = """Ești dispecerul de urgență pentru o comunitate (Neighbour In Need).
Politica ta de decizie:
1. Dacă source=watch_button -> decizi "verify" (răspunzi: "Ai apăsat butonul de urgență. Ești bine? Spune DA sau AJUTOR."). Dacă primești timeout -> escalate.
2. Dacă source=watch_fall cu fallConfidence >= 0.8 sau watch_hr cu hr < 40 sau hr < 0.6*baseline -> "verify" cu text specific. Fără răspuns -> escalate.
3. escalate = obține membrii din apropiere (get_nearby_members) -> alege după disponibilitate, distanță, skills potrivite, hasCar dacă e cazul. Scrie un brief (max 3 propoziții). Actualizează tichetul (update_ticket cu assignedTo). Notifică membrul și grupul. Dacă nimeni < 800m -> notify_group + call_emergency dacă severity=critical.
4. Răspuns "da / sunt bine / fals" -> fals_alarm, notify_group(cancelled).
"""

dispatcher_agent = Agent(
    model=model,
    tools=[get_nearby_members, create_ticket, update_ticket, notify_group, notify_member, speak_to_user, call_emergency, find_recent_tickets],
    system_prompt=SYSTEM_PROMPT
)


def run_dispatcher(sos_payload: dict) -> dict:
    """Punct de intrare principal pentru payload de SOS.

    Returnează întotdeauna {ok, ticket_id, responder, motiv, istoric}. Nu ridică excepții pentru
    payload invalid — le transformă în ok=False cu motiv explicit, ca apelantul (handler.py) să
    poată răspunde 400 fără try/except suplimentar.
    """
    istoric: List[Dict[str, Any]] = []

    try:
        validate_sos_payload(sos_payload)
    except PayloadValidationError as e:
        return {
            "ok": False,
            "ticket_id": None,
            "responder": None,
            "motiv": str(e),
            "istoric": istoric,
        }

    group_id = sos_payload["group_id"]
    uid = sos_payload["uid"]
    lat = sos_payload["lat"]
    lng = sos_payload["lng"]
    source = sos_payload.get("source", "unknown")
    text = sos_payload.get("text")
    ts = sos_payload.get("ts")
    required_skill = sos_payload.get("requiredSkill")

    _log_step(istoric, "primit", f"sursă={source}, uid={uid}, text={text!r}, ts={ts!r}")

    ticket_id = create_ticket(group_id, sos_payload)
    _log_step(istoric, "tichet_creat", ticket_id)

    members = get_nearby_members(group_id, lat, lng)
    _log_step(istoric, "cautare_membri", f"{len(members)} membri găsiți")

    responder = select_responder(members, required_skill=required_skill)

    if responder is None:
        update_ticket(group_id, ticket_id, {"status": "neacoperit"})
        notify_group(group_id, ticket_id, "neacoperit")
        _log_step(istoric, "fallback", "niciun membru disponibil — grup notificat, tichet neacoperit")
        return {
            "ok": True,
            "ticket_id": ticket_id,
            "responder": None,
            "motiv": "niciun membru disponibil în apropiere",
            "istoric": istoric,
        }

    update_ticket(group_id, ticket_id, {"status": "asignat", "assignedTo": responder.get("uid")})
    notify_member(responder.get("uid"), "Alertă SOS", f"Ai fost desemnat responder pentru tichetul {ticket_id}")
    notify_group(group_id, ticket_id, "asignat")
    _log_step(istoric, "asignat", f"responder={responder.get('uid')}")

    return {
        "ok": True,
        "ticket_id": ticket_id,
        "responder": responder,
        "motiv": f"cel mai apropiat responder disponibil ({responder.get('distance')} m)",
        "istoric": istoric,
    }
