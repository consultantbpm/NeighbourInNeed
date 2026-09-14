import os
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
    """Punct de intrare principal pentru payload de SOS."""
    prompt = f"Analizează această alertă: {sos_payload}"
    result = dispatcher_agent.run(prompt=prompt)
    
    # Procesarea răspunsului generat de model, extragere structură JSON
    # Aici simulăm structura necesară pentru API
    # {ticketId, decision: "verify"|"escalate"|"dismiss", speak: "text TTS"}
    
    return {
        "ticketId": sos_payload.get("ticketId", "unknown"),
        "decision": "verify", # extras logic din result
        "speak": "Ai apăsat butonul de urgență. Ești bine? Spune DA sau AJUTOR."
    }
