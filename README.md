# Neighbour In Need

**Agents for Humans Hackathon — Good Neighbor Agents track.**
An AI agent that turns a one-press SOS from a smartwatch or phone into coordinated help from the people
nearby who can actually give it: the neighbours, relatives and volunteers of a local care group.

## The problem

When an elderly or vulnerable person needs help, the people best placed to respond are usually a few hundred
metres away: a neighbour with a car, a relative who is a nurse, a volunteer from the parish or the block
association. Today that help is coordinated by phone calls and group chats, slowly, and often nobody knows
who is free, who is close, or who already went. Emergency services are for emergencies; most calls for help
are not, and they fall through the cracks.

## What the agent does

1. The person presses SOS on the watch or phone (or a caregiver reports a medication question).
2. The mobile app routes the alert: Wear OS data layer → phone → local network (mDNS) or SMS fallback when
   there is no internet.
3. A **Strands Agents SDK** agent (`backend_python/dispatcher.py`) receives the alert with location and context,
   finds group members nearby who are available now, opens a ticket, picks the best responder by distance and
   skills, and notifies the group. A second agent (`backend_python/meds.py`) handles medication questions from a
   photo of the box or prescription and the member's profile.
4. Every step is recorded on the ticket so the group knows who is going and what happened.

## Architecture

```
 Wear OS watch ──(Data Layer)──▶ Android phone app ──(mDNS / SMS fallback)──▶ Dispatcher agent
                                        │                                          │
                                        └── Firebase (group, members, tickets) ◀───┘
                                                                                   │
                                                              Strands Agents SDK + Bedrock model
                                                              tools: get_nearby_members, create_ticket,
                                                                     update_ticket, notify_group
```

- `mobile/` — React Native app: alert routing (`AlertRoutingService.js`), Wear OS bridge
  (`WearDataLayerService.js`), SMS fallback (`SmsFallbackService.js`), Firebase config and data model.
- `backend_python/dispatcher.py` — the SOS dispatcher agent (Strands `Agent` + `@tool` functions, Bedrock model).
- `backend_python/meds.py` — the medication-assistant agent.
- `backend_python/handler.py` — AWS Lambda entry point; `local_server.py` — the same handler served locally
  over FastAPI with mDNS advertisement, used for the demo.
- `backend_python/tests/test_policy.py` — policy tests.

## Run the demo locally

```bash
cd backend_python
pip install strands-agents fastapi uvicorn zeroconf
python local_server.py        # listens on :8000 and advertises itself on the local network
```

Then press SOS on the watch or phone, or simulate it with `SIMULEAZA_SOS_CEAS.ps1`.

## Status and honesty note

This is a hackathon prototype. The Firebase tools in the dispatcher return fixture data where noted with
`TODO`; the agent flow, routing and fallback paths are real. No benchmark figures are claimed for this project.

## License

MIT — see `LICENSE`.
