# disruption_finding.py

[status]: [done]
[last updated]: [21-09-2026]

**Path:** `backend/app/evaluator/DisruptionFinding.py`

## Context
`BoardEvaluator.evaluate` needs an output shape for "one disruption found on a board snapshot." 

Named `DisruptionFinding` rather than the more generic `Finding` name because every field here is disruption-specific. A broader vision includes other kinds of findings later (resource, followup or whatnot), and those would get their own type rather than overloading this one.

## Purpose
Represent one disruption result from `BoardEvaluator.evaluate`, already collapsed for once-per-turn scope.

## Main Components

- `DisruptionFinding` — frozen dataclass: `owner` (`Player`), `card_name` (`str`), `category` (`DisruptionCategory`), `disruption_type` (`DisruptionType`), `opt_scope` (`OncePerTurnScope`), `instance_count` (`int`).
- `owner` — a `BoardState` snapshot has two players' worth of zones; a finding needs to say whose side it came from.
- `instance_count` — kept meaningful and consistent across both OPT scopes rather than only mattering for `HARD`. For `SOFT`-scope cards, `BoardEvaluator` emits one `DisruptionFinding` per instance (`instance_count = 1` each) rather than a single finding with a higher count, so a caller can treat `len(findings)` as "how many independent things are live" without special-casing `opt_scope`. For `HARD`-scope cards, all matching copies collapse into one finding with `instance_count` set to however many were found.

## How It Fits In
Depends on `Player` (`app.core.Player`) and the `DisruptionType`/`OncePerTurnScope`/`DisruptionCategory` enums (`app.type_defs.type_disruption`). Constructed only by `evaluator.BoardEvaluator._findings_for_player`; nothing else builds one.

## Notes
Pure data, no methods — ranking/summarizing/displaying findings is presentation-layer concern, out of scope for this type.

A shared base type across finding types (disruption, resources) is a reasonable generalisation to make once those other kinds actually get built (see `_docs/workflow.md`'s Evaluation Layer section) — not attempted preemptively here.
