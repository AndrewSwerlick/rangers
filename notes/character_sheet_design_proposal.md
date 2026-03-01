# Character Sheet Design Proposal — The Rangers

## Understanding the Game

The Rangers is a one-shot TTRPG (120-180 minutes) where players are park rangers defending humanity's last havens — former state and national parks — against supernatural threats spawned by an alien invasion. The game uses real park maps as game boards, with actual locations (fire towers, dams, ranger stations) serving mechanical roles.

The emotional core isn't about victory. It's about *what you choose to save when you can't save everything*. The three-act structure mirrors this arc:

1. **Prep Phase** — Collaborative worldbuilding. Rangers answer prompts about their past, assign meaning to map locations, and spend tokens on defenses. This is where players invest emotionally in the world they'll defend.

2. **Defense Phase** — Tower defense mechanics. Waves of escalating threats assault the park. Rangers move along trails, man locations, and make tactical decisions under increasing pressure. Resources drain. Positions fall.

3. **Desperation Phase** — When primary objectives fail, rangers make one last stand for personal stakes. Victory is reframed: not "defeat the enemy" but "hold long enough for the evacuation" or "destroy the artifact before they take it." Sacrifice becomes the currency of heroism.

The character sheet must support all three phases while carrying the emotional weight of a ranger's identity.

---

## Front/Back System

The sheet uses two sides with clear separation of concerns:

**Front (Identity & Status):** Everything about *your ranger* — who they are, what state they're in, what they can do. This is the side players look at most often. It should breathe, feel personal, and track the ranger's deteriorating condition as play progresses.

**Back (Rules Reference):** Everything about *how to play* — action menus, damage formulas, injury consequences, desperation moves. Dense, information-rich, consulted when needed. This is the "flip to check" side.

This separation mirrors the game's emotional structure:
- Front = the ranger as *person* (narrative investment)
- Back = the ranger as *game piece* (mechanical clarity)

---

## Typography

Three visual registers map onto the game's emotional structure:

| Register | Typography | Emotional Mode | Usage |
|----------|-----------|----------------|-------|
| **Monumental** | Josefin Sans Bold | Institutional reverence | Headers, title, phase names |
| **Scholarly** | EB Garamond | Precise observation | Rules text, ability descriptions |
| **Personal** | Caveat / player handwriting | Intimate, handwritten | Prompts (Caveat); player entries (their hand) |

The character sheet is an *official document* (WPA monumentalism) containing *field observations* (naturalist guide precision) annotated by a *specific individual* (handwritten personal voice).

---

## Color Palette (WPA-Inspired)

```
parkbrown   #593C1F   Headers, borders, institutional elements
parkgreen   #2D572C   Accents (optional)
mutedtext   #646464   Reference text, secondary information
rulelight   #B4B4B4   Writing lines
```

---

## Front Layout

The front focuses on identity and status. Trackers are simple circles without inline explanations — rules live on the back.

### Front — Full Layout
```
+==============================================================================+
‖  T H E   R A N G E R S              FIELD SERVICE RECORD    [mountain silh.] ‖
+==============================================================================+
|                         |                                                    |
|   +-----------------+   |   ARCHETYPE                                        |
|   |                 |   |   Name: ______________________________________     |
|   |                 |   |   ________________________________________________ |
|   |    [PORTRAIT]   |   |   (brief archetype description / flavor text)      |
|   |                 |   +----------------------------------------------------+
|   |    (player      |   |                    A C T I O N S                   |
|   |     sketch)     |   +--------------+--------------+----------------------+
|   |                 |   |     PREP     |   DEFENSE    |     DESPERATION      |
|   |                 |   +--------------+--------------+----------------------+
|   +-----------------+   |              |              |                      |
|                         | ____________ | ____________ | ____________________ |
|   RANGER NAME           |              |              |                      |
|   ___________________   | ____________ | ____________ | ____________________ |
|                         |              |              |                      |
+-------------------------+--------------+--------------+----------------------+
|                         |                                                    |
|  HARM       ○  ○  ○     |   CHARACTER                                        |
|                         |                                                    |
+-------------------------+   What were you running from?                      |
|                         |   ________________________________________________ |
|  EXHAUSTION ○  ○  ○     |   ________________________________________________ |
|                         |   ________________________________________________ |
+-------------------------+   ________________________________________________ |
|                         |   ________________________________________________ |
|  TOKENS  |______|       |   ________________________________________________ |
|  (tally or physical)    |                                                    |
|                         |                                                    |
+-------------------------+----------------------------------------------------+
```

**Token Tracking:** Physical tokens (chips, coins, stones) are preferred — tangible, visible to the table, satisfying to spend. The sheet provides a small tally box as fallback for groups without physical tokens.
### Front — Section Details

**Header Strip**
- "THE RANGERS" wordmark in Josefin Sans Bold, letterspaced, white on park brown
- "FIELD SERVICE RECORD" subtitle
- Mountain silhouette placeholder (right side)

**Left Column**
- **Portrait Box** — Naturalist field guide style frame, blank for player sketch
- **Ranger Name** — Label + writing line below portrait
- **HARM** — Label + 3 circles (no explanation text)
- **EXHAUSTION** — Label + 3 circles (no explanation text)
- **TOKENS** — Small tally box for groups without physical tokens

**Right Section — Upper**
- **ARCHETYPE** — Name field spanning the width
- **ACTIONS Triptych** — Three columns (PREP / DEFENSE / DESPERATION)
  - Each column has ruled lines for writing that phase's archetype ability
  - This IS where archetype abilities go — no separate archetype box needed

**Right Section — Lower**
- **CHARACTER** — Full-width section for backstory
  - Pre-printed prompt in Caveat: "What were you running from?"
  - Multiple ruled lines for player writing

---

## Back Layout

The back is dense and functional. Organized into logical reference blocks players can scan quickly.

### Back — Full Layout
```
+==============================================================================+
‖  T H E   R A N G E R S              FIELD OPERATIONS GUIDE                   ‖
+==============================================================================+
|                                          |                                   |
|   YOUR TURN: 3 ACTIONS                   |   INJURY TRACK                    |
|   ────────────────────                   |   ────────────                    |
|                                          |                                   |
|   SAFE ACTIONS (auto-succeed)            |   HEALTHY                         |
|   • Move along trails                    |   Full movement options           |
|   • Move on unoccupied roads             |                                   |
|   • Use location ability                 |   1 INJURY                        |
|   • Setup chokepoint                     |   No bushwhacking (off-trail)     |
|   • Hold position (gain 1 token)         |   Trails and roads only           |
|                                          |                                   |
|   RISKY ACTIONS (roll d6)                |   2 INJURIES                      |
|   • Attack the wave                      |   Roads only — no trails          |
|   • Bushwhack (off-trail move)           |   High capture risk               |
|                                          |                                   |
|                                          |   3 INJURIES                      |
|   ROLL OUTCOMES                          |   Cannot move                     |
|   ─────────────                          |   Must hold or be captured        |
|   1–3  Fail — take harm                  |   Rolling 6 = automatic capture   |
|   4–5  Mixed — succeed but take harm     |                                   |
|   6    Clean success                     +-----------------------------------+
|                                          |                                   |
|   Advantage: Roll 2d6, take higher       |   EXHAUSTION                      |
|   Disadvantage: Roll 2d6, take lower     |   ──────────                      |
|                                          |   Your dice pool for risky rolls  |
+------------------------------------------+   Base: 3d6 (3 empty circles)     |
|                                          |   Mark circles as you exhaust     |
|   ATTACK DAMAGE                          |   Roll only unmarked dice         |
|   ─────────────                          |   Minimum: 1d6                    |
|   Base damage: 1 momentum                |                                   |
|                                          |   When you take harm, choose:     |
|   Bonuses:                               |   • Mark 1 injury, OR             |
|   • Your archetype bonus: +1             |   • Mark 1 exhaustion             |
|   • Location bonus: +1                   |                                   |
|   • Archetype + location synergy: +2     +-----------------------------------+
|                                          |                                   |
|   Maximum damage: 3 momentum             |   RECOVERY (between waves)        |
|                                          |   ────────                        |
+------------------------------------------+   Each ranger gets 1 point:       |
|                                          |   • Heal 1 injury                 |
|   BREACH DEFENSE                         |   • Clear 1 exhaustion            |
|   ──────────────                         |   • Restore 1 obstacle            |
|   When wave assaults your position,      |   • Use location recovery bonus   |
|   roll d6:                               |                                   |
|                                          +-----------------------------------+
|   1–3  REPELLED                          |                                   |
|        Wave takes damage, you're safe    |   TOKENS                          |
|        Location holds                    |   ──────                          |
|                                          |   Earn: Prep prompts, holding,    |
|   4–5  CONTESTED                         |         adversity, narrative      |
|        Wave takes damage                 |                                   |
|        Choose: injury / exhaustion /     |   Spend (Prep): Traps, barricades,|
|                retreat (lose location)   |         fortifications            |
|                                          |                                   |
|   6    BREAKTHROUGH                      |   Spend (Desperation): Heroic     |
|        Must retreat to adjacent location |         moves (see below)         |
|        If cannot retreat → captured      |                                   |
|        Wave pays +2 to secure location   |                                   |
|                                          |                                   |
+------------------------------------------+-----------------------------------+
|                                                                              |
|   DESPERATION MOVES (Act 3 Only — Available to All Rangers)                  |
|   ─────────────────────────────────────────────────────────                  |
|                                                                              |
|   LAST STAND (2 tokens)                  HOLD THE LINE (2 tokens)            |
|   Deal 3 damage automatically            Location impregnable for 1 wave     |
|   Take 1 injury                          turn — all breaches auto-fail       |
|                                                                              |
|   AGAINST ALL ODDS (1 token)             NOT TODAY (1 token)                 |
|   Auto-succeed any risky action          Negate an injury you just took      |
|                                                                              |
|   ENVIRONMENTAL CATASTROPHE (3 tokens)   THE LONG GOODBYE (3 tokens)         |
|   Remove 1 wave token from board         Willing capture — remove 2 tokens   |
|   Describe what you destroy              Describe your final stand           |
|                                                                              |
+------------------------------------------------------------------------------+
```

### Back — Section Breakdown

**Left Column (Action-focused)**
- **YOUR TURN** — 3-action economy, safe vs risky action lists
- **ROLL OUTCOMES** — d6 results + advantage/disadvantage
- **ATTACK DAMAGE** — Formula with bonuses (1 + bonuses, max 3)
- **BREACH DEFENSE** — Reactive roll outcomes when defending

**Right Column (Status-focused)**
- **INJURY TRACK** — Movement restrictions at each level (the core consequence)
- **EXHAUSTION** — Dice pool mechanic, harm choice
- **RECOVERY** — Between-wave options
- **TOKENS** — Earning and spending overview

**Bottom Strip (Desperation)**
- **DESPERATION MOVES** — All six universal moves with costs
- Full-width to emphasize Act 3's dramatic shift

---

## Typography Specification

### Front

| Element | Font | Size | Treatment |
|---------|------|------|-----------|
| "THE RANGERS" | Josefin Sans Bold | 24-28pt | Letterspaced, white on brown |
| Section headers (HARM, ACTIONS, etc.) | Josefin Sans Bold | 10-11pt | All caps, park brown |
| "ARCHETYPE:" label | Josefin Sans Bold | 10pt | All caps |
| Column headers (PREP, DEFENSE, etc.) | Josefin Sans Bold | 10pt | All caps, centered |
| Pre-printed prompt | Caveat | 11pt | Italic, muted |
| Writing lines | — | — | Light gray rules for player handwriting |

### Back

| Element | Font | Size | Treatment |
|---------|------|------|-----------|
| "FIELD OPERATIONS GUIDE" | Josefin Sans Bold | 18pt | Letterspaced |
| Section headers | Josefin Sans Bold | 10pt | All caps, with underline |
| Body text | EB Garamond | 8pt | Dense but readable |
| Roll numbers (1-3, 4-5, 6) | EB Garamond Bold | 9pt | Stand out for scanning |
| Desperation move names | Josefin Sans Bold | 9pt | Distinguish from descriptions |
| Token costs | EB Garamond Bold | 8pt | Parenthetical |

---

## Implementation Notes

### Two-Sided Printing
- Letter paper, landscape orientation
- Front: identity-focused, generous spacing
- Back: reference-focused, information-dense

### PDF Generation
- Single PDF with two pages (front, back)
- LuaLaTeX for Google Fonts support (Josefin Sans, EB Garamond, Caveat)
- TikZ for precise layout control

### Player Experience
- Hand out sheets face-up (front showing)
- Players fill in front during prep phase
- Flip to back when rules questions arise
- By mid-game, most players internalize back content

---

## Summary

| Aspect | Front | Back |
|--------|-------|------|
| **Purpose** | Identity & status | Rules reference |
| **Content** | Portrait, name, archetype abilities, backstory, trackers | Actions, damage, defense, injury, desperation |
| **Density** | Breathing room | Information-dense |
| **Interaction** | Written on | Consulted |
| **Register** | Personal + Monumental | Scholarly + Monumental |

The front is *your ranger*. The back is *how to play*.
