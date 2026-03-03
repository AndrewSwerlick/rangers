# Essential Rules for Character Sheet — Research Notes

## Overview

After reviewing all rules documents, this analysis identifies what mechanics players need at-a-glance during play, compares against the current character sheet implementation, and recommends changes.

---

## Current Character Sheet Contents

### What's There Now
- **HARM**: 3 circles + brief explanation (disadvantage, movement, incapacitated)
- **EXHAUSTION**: 3 circles + "Roll unfilled circles (base 3d6)"
- **ROLLS REF**: d6 outcomes (1-3 fail, 4-5 mixed, 6 success) + safe/risky note
- **ACTIONS triptych**: PREP / DEFENSE / DESPERATION columns with ruled lines
- **ARCHETYPE**: Prep bonus, Defense ability, Desperation move fields
- **CHARACTER**: Backstory section with prompt

---

## Rules Analysis: What Players Actually Need

### 1. HARM/INJURY TRACK — **NEEDS REVISION**

**Current sheet says:**
- 1 Harm: Disadvantage on physical actions
- 2 Harm: Movement halved; can't sprint
- 3 Harm: Incapacitated — captured or dying

**Actual rules (from ranger_turns.md):**
The injury track has **movement-based consequences**, not generic disadvantage:

| Injury Level | Movement Restriction | Capture Risk |
|--------------|---------------------|--------------|
| **Healthy** | Full movement options | Low |
| **1st Injury** | No bushwhacking (off-trail) | Moderate if roads blocked |
| **2nd Injury** | Can ONLY use roads (no trails) | High if roads wave-controlled |
| **3rd Injury** | Cannot move at all | Rolling 6 = automatic capture |

**Recommendation:** Rewrite HARM explanation to focus on movement restrictions. This is the core tactical consequence players need to track.

---

### 2. EXHAUSTION — **MOSTLY CORRECT**

**Current sheet says:** "Roll unfilled circles (base 3d6). Mark when you push, sprint, or overexert."

**Actual rules:**
- Rangers start with 3d6 dice pool
- Exhaustion shrinks the pool (minimum 1d6)
- Can choose exhaustion instead of injury when taking harm

**Recommendation:** Minor tweak — clarify it's a choice when taking harm:
> "Dice pool for risky actions (base 3d6). When you take harm, you may mark exhaustion instead of injury."

---

### 3. ROLLS REF — **NEEDS EXPANSION**

**Current sheet shows:** Basic d6 outcomes

**Missing critical info:**
- **Advantage/Disadvantage**: Roll 2d6, take higher/lower (several abilities grant this)
- **What triggers rolls**: Only risky actions require rolls

**Recommendation:** Keep current text but ensure advantage/disadvantage is mentioned somewhere (possibly in archetype ability descriptions).

---

### 4. ACTION ECONOMY — **NOT ON SHEET**

**This is a significant gap.** Players need to know:

**3 Actions Per Turn:**
- Can mix safe and risky actions
- No limit on safe actions
- Multiple risky actions = high risk

**Safe Actions (auto-succeed):**
- Move on trails
- Move on unoccupied roads
- Use location ability
- Setup chokepoint
- Hold (gain 1 token + narrative moment)

**Risky Actions (require d6 roll):**
- Attack wave
- Bushwhack (off-trail movement)

**Recommendation:** Add a compact ACTION MENU to the sheet, possibly replacing some of the ruled lines in the ACTIONS columns, or as a separate reference box.

---

### 5. DAMAGE FORMULA — **NOT ON SHEET**

**Players need to know how attack damage works:**

Base damage: **1 momentum**

Bonuses:
- Certain ranger archetypes: **+1**
- Certain locations: **+1**
- Archetype + location synergy: **+2**

**Maximum damage: 3 momentum per attack**

**Recommendation:** Add a small DAMAGE box or include in ROLLS REF:
> "Attack damage: 1 + bonuses (max 3)"

---

### 6. BREACH DEFENSE — **NOT ON SHEET**

When defending a location/barricade against wave assault:

| Roll | Result | Wave Cost | Ranger Consequence |
|------|--------|-----------|-------------------|
| 1-3 | Repelled | 1 + bonuses | None |
| 4-5 | Contested | 1 + bonuses | Choose: injury, exhaustion, or retreat |
| 6 | Breakthrough | 1 + bonuses | Must retreat (or captured) |

**Recommendation:** This is reactive (happens during wave turn), so players need quick reference. Consider adding to ROLLS REF or a separate DEFENSE box.

---

### 7. RECOVERY OPTIONS — **NOT ON SHEET**

Between waves, each ranger gets **1 recovery point**:
1. Recover 1 injury
2. Clear 1 exhaustion
3. Restore one trap/obstacle
4. Invoke location recovery bonus

**Recommendation:** Could be a small box, but may be lower priority since it only happens between waves and GM can remind players.

---

### 8. DESPERATION MOVES — **PARTIAL**

Current sheet has a DESPERATION column and archetype desperation move field.

**Core Desperation Moves (available to all in Act 3):**

| Move | Cost | Effect |
|------|------|--------|
| **Last Stand** | 2 tokens | 3 damage auto, take 1 injury |
| **Environmental Catastrophe** | 3 tokens | Remove 1 token from board |
| **Against All Odds** | 1 token | Auto-succeed any risky action |
| **Hold the Line** | 2 tokens | Location impregnable for 1 wave turn |
| **Not Today** | 1 token | Negate injury just taken |
| **The Long Goodbye** | 3 tokens + capture | Remove 2 tokens from board |

**Recommendation:** These are universal moves, not archetype-specific. Consider:
- Adding a compact desperation move reference
- Or noting "See Desperation Move reference card" if a separate handout is preferred

---

### 9. TOKEN ECONOMY — **NOT ON SHEET**

Players earn tokens through:
- Narrative contributions in prep
- Holding position (1 token + narrative moment)
- Adversity during defense phase

Tokens can be spent on:
- Prep phase defenses (traps, barricades, fortifications)
- Desperation moves (Act 3 only)

**Recommendation:** A TOKEN tracker with a few circles would help players track their personal token count.

---

## Priority Recommendations

### High Priority (Essential for Play)
1. **Fix HARM explanation** — Movement restrictions, not generic disadvantage
2. **Add ACTION MENU** — Safe vs risky actions list
3. **Add DAMAGE formula** — "1 + bonuses (max 3)"

### Medium Priority (Helpful Reference)
4. **Add BREACH DEFENSE outcomes** — Reactive roll during wave assault
5. **Add TOKEN tracker** — Simple circles to track earned tokens
6. **Expand EXHAUSTION note** — Clarify it's a harm choice

### Lower Priority (Nice to Have)
7. **Recovery options** — GM can remind, less urgent
8. **Desperation moves list** — Could be separate reference card

---

## Layout Considerations

The current left column has room constraints. Options:
1. **Shrink portrait further** — Gain ~0.5" more vertical space
2. **Use smaller font** — Current HARM EXPLAIN is 7pt, could go to 6pt for dense reference
3. **Move some info to right section** — ROLLS REF could merge with ACTIONS area
4. **Create back side** — Two-sided sheet with reference on back

The ACTIONS triptych currently has ruled lines for writing abilities. Consider:
- Fewer lines + more reference text
- Pre-printed action menus in each column
- Separate "Actions at a glance" reference card

---

## Questions for Design Decision

1. Should the sheet be **single-sided** (constraints force prioritization) or **two-sided** (more reference space)?

2. Should **desperation moves** be on the character sheet or a **separate reference card**?

3. Is the **portrait box** essential, or could that space be used for mechanics?

4. Should archetypes have **pre-printed abilities** or blank lines for player writing?

---

## Appendix: Source Documents Reviewed

- `notes/overview.md` — Core concept, 3-act structure, injury system
- `notes/ranger_turns.md` — Action economy, movement, combat, injury track details
- `notes/wave_turn.md` — Wave mechanics, breach defense, obstacles
- `notes/prep_phase.md` — Token economy, obstacle types, prep spending
- `notes/assault_phase.md` — Phase structure, recovery
- `notes/desperation_phase.md` — Act 3 mechanics, desperation moves
- `notes/ranger_archetypes.md` — 6 archetypes with abilities
- `notes/locations.md` — 8 location types with bonuses
