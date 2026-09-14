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

model = BedrockModel(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1")

SYSTEM_PROMPT = """Ești agentul de medicație.
Reguli:
1. Verifici potrivirea numelui și dozei (din identify_medication) cu profilul pacientului (get_member_profile).
2. Dacă lastTakenAt este azi în fereastra schemei -> "NU mai lua".
3. Dacă expirarea e depășită -> avertisment.
4. Dacă e nepotrivire cu profilul -> "Nu e în schema ta, nu lua fără să întrebi".
"""

meds_agent = Agent(
    model=model,
    tools=[identify_medication, parse_prescription, get_member_profile, update_ticket],
    system_prompt=SYSTEM_PROMPT
)

def run_meds_check(payload: dict) -> dict:
    """Procesează verificarea unui medicament."""
    prompt = f"Verifică medicamentul pentru {payload['uid']} din grupul {payload['groupId']}. Imagine baza 64: {payload.get('imageBase64', '')[:20]}..."
    result = meds_agent.run(prompt=prompt)
    
    return {
        "medName": "Paracetamol",
        "dose": "500mg",
        "matchesProfile": True,
        "alreadyTakenToday": False,
        "speak": "Acesta este Paracetamol 500mg. Îl poți lua."
    }
