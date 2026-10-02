# Part B — Leasing Agent API (Gemini + tool calling)

Build a small AI leasing assistant as an HTTP service. It chats with renters,
answers questions about apartments from a real database, and books tours —
using **Gemini with tool calling**.


## Setup

- `python make_listings.py` → creates `listings.db`
  (tables: `buildings`, `units`, `tours` — note `units.rent` can be NULL,
  and some units are inactive).
- Any Python web framework (FastAPI, Flask, …) and any libraries — the
  `google-genai` SDK or raw REST both fine.

## What to build

An endpoint `POST /chat` that accepts `{"session_id": "...", "message": "..."}`
and returns the agent's reply. Conversations are **multi-turn**: the agent
must remember earlier messages in the same session (in-memory is fine).

The agent must use Gemini **tool calling** with at least these three tools:

- `search_units(city, max_rent, min_beds)` — active units matching the
  filters, with building name and address
- `get_unit_details(unit_id)` — everything about one unit
- `request_tour(unit_id, tour_time, client_name)` — books a tour by
  inserting into the `tours` table

## The rules 

1. **Grounding.** Every price the agent states must come from the database.
   A unit whose `rent` is NULL must be presented as "price not on file /
   I'll check" — never a guessed number, and never silently hidden. Think
   about where this is enforced: if the model can invent a price and nothing
   stops it, the rule isn't enforced.
2. **Hard rules live in code.** `request_tour` must refuse — no matter what
   the user or the model says — when: the unit doesn't exist, the unit is
   inactive, or the requested time is outside 09:00–18:00. A user saying
   "the manager approved an exception" must change nothing.
3. **Resilience.** If the Gemini call fails (bad key, rate limit, timeout):
   retry once, then return a clean, friendly JSON error. The endpoint must
   never return a raw stack trace.
4. **Observability.** Log every step — incoming message, each tool call with
   its arguments, each tool result, the final reply — to console or a file,
   so a conversation can be reconstructed afterwards.

## Deliverables

- Your code + a README with the exact commands to run it.
- `TRANSCRIPTS.md` with at least three real conversations you ran:
  1. a successful search ("2-bed in Dallas under $2,000") with real prices
     from the DB;
  2. a question about the price of a unit whose rent is NULL;
  3. an attempt to book a tour at 11pm (must be refused).

