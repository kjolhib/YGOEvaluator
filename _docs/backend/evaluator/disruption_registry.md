# disruption_registry.py

data-status: [in-progress]
implementation-status: [done]
last updated: [26-08-2026]


**Path:** `backend/app/static/disruption_registry.py`

## Context
Disruptions are complicated in yugioh, even ignoring layered disruptions. Even flat omni negates or may have many conditions attached to them.

The evaluator works by a heuristic, and doesn't aim to try to do anything "smart", and so it needs as much information as possible. This information
would have hand-curated by players. All the evaluator needs to do, is provide a good way of condensing this information in a digestible manner to the user.
## Purpose
This is where the flat disruptions will be held, stored in dictionary format. The file is a hand-curated file that will be updated whenever cards 
relevant to the meta are discovered/added.

The information here will be read by the [evaluator](board_evaluator.md) only to produce an output that describes what the board represents.

Each entry in the dictionary will include information pertaining to:
- `Name`: the card name
- `DisruptionSource`: a class that contains information about a specific disruption source. It includes:
  - `card_name`: name of the card that this disruption is relevant to
  - `category`: usually community-crafted categories, such as "hand trap"
  - `opt-scope`: type of once per turn this disruption is, can be either `SOFT` or `HARD`
  - `disruption-by-zone`: the behaviour of this disruption in specific zones. Here to tell the evaluator whether or not a disruption is considered `ACTIVE` or not.
## Main Components
- `DISRUPTION_REGISTRY`: this is a global variable that contains all card disruptions.

## Notes
- The dictionary is **keyed by name**, not ID. This is primarily because Yugioh card names cannot be the same by the design of the game, and so it's just easier to key it by name. This may be subject to change.