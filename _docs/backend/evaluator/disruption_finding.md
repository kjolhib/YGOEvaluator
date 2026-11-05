# disruption_finding.py

[status]: [done]
[last updated]: [20-10-2026]

**Path:** `backend/app/evaluator/disruption_finding.py`

## Context
`BoardEvaluator.evaluate` needs an output shape for "one disruption found on a board snapshot." 

Named `DisruptionFinding` rather than the more generic `Finding` name because every field here is disruption-specific. A broader vision includes other kinds of findings later (resource, followup or whatnot), and those would get their own type rather than overloading this one.

Findings are produced **per effect**, not per card. A card with several live effects contributes several findings (see Main Components).

## Purpose
Represent one disruption result from `BoardEvaluator.evaluate`, already collapsed for once-per-turn scope.

## Main Components

- `DisruptionFinding` — frozen dataclass: `owner` (`Player`), `card_name` (`str`), `effect_label` (`str`), `categories` (`list[DisruptionCategory]`), `disruption_type` (`DisruptionType`), `opt_scope` (`OncePerTurnScope`), `instance_count` (`int`).
- `owner` — a `BoardState` snapshot has two players' worth of zones; a finding needs to say whose side it came from.
- `effect_label` and `categories` — which effect of the card this finding is about, and what kinds of disruption that effect has. These, along with `opt_scope`, are copied from the `DisruptionEffect` that produced the finding, not from the card.
- `instance_count` — kept meaningful and consistent across both OPT scopes rather than only mattering for `HARD`. Collapsing is decided by the **effect's** `opt_scope`:
  - `SOFT` effect: one `DisruptionFinding` per copy (`instance_count = 1` each), so a caller can treat `len(findings)` as "how many independent things are live" without special-casing `opt_scope`.
  - `HARD` effect: all matching copies collapse into one finding with `instance_count` set to however many were found.
- A card with several live effects emits one finding group per effect. For example a face-up Baronne de Fleur gives two findings (omni negation, targeted destruction); two copies of her give two findings, each with `instance_count == 2`, because both of her effects are hard-OPT.

## How It Fits In
Depends on `Player` (`app.core.player`) and the `DisruptionType`/`OncePerTurnScope`/`DisruptionCategory` enums (`app.static.type_defs.type_disruption`). Constructed only by `app.evaluator.board_evaluator` (the `_find` helper, called from `_findings_for_player`); nothing else builds one.

## Notes
Pure data, no methods — ranking/summarizing/displaying findings is presentation-layer concern, out of scope for this type.

`effect_label` identifies the effect only within its card, so a finding is identified by `(owner, card_name, effect_label, disruption_type)`.

A shared base type across finding types (disruption, resources) is a reasonable generalisation to make once those other kinds actually get built (see `_docs/workflow.md`'s Evaluation Layer section) — not attempted preemptively here.
