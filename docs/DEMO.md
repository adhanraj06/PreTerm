# PreTerm — exhaustive product reference

This document is a **product-level** description of PreTerm: what each screen is for, what every control does, what the user should understand when they see a number or a label, and how workflows chain together. It is written for **demos, training, product reviews, and writing marketing copy**—not for implementers tracing API calls.

If you are onboarding a new teammate, you can ask them to read this once, then walk the **numbered demo script** at the end with the app open.

---

## Table of contents

1. [What PreTerm is (one paragraph)](#what-preterm-is-one-paragraph)
2. [Vocabulary (read this first)](#vocabulary-read-this-first)
3. [What is saved where (persistence)](#what-is-saved-where-persistence)
4. [Routes you can land on](#routes-you-can-land-on)
5. [Boot and auth behavior](#boot-and-auth-behavior)
6. [Sign in](#sign-in)
7. [Register](#register)
8. [The workstation shell (every authenticated page)](#the-workstation-shell-every-authenticated-page)
9. [Market Copilot (right column)](#market-copilot-right-column)
10. [Monitor — contract grid](#monitor--contract-grid)
11. [Monitor — contract detail](#monitor--contract-detail)
12. [Watchlists](#watchlists)
13. [Headlines](#headlines)
14. [Research](#research)
15. [Planner](#planner)
16. [Settings](#settings)
17. [Cross-desk workflows (storyboards)](#cross-desk-workflows-storyboards)
18. [Validation and disabled rules (quick matrix)](#validation-and-disabled-rules-quick-matrix)
19. [Empty states and system messages (catalog)](#empty-states-and-system-messages-catalog)
20. [Visual language (what colors and badges mean)](#visual-language-what-colors-and-badges-mean)
21. [Personas — “a day in the life”](#personas--a-day-in-the-life)
22. [Extended demo script (step-by-step)](#extended-demo-script-step-by-step)
23. [FAQ (user confusion)](#faq-user-confusion)
24. [Appendix — sample content shipped in the UI](#appendix--sample-content-shipped-in-the-ui)
25. [Reading order (how to scan each screen)](#reading-order-how-to-scan-each-screen-without-getting-lost)
26. [Worked example — reading one card](#worked-example--reading-one-card-in-english)
27. [Narration cues (demo talk track snippets)](#narration-cues-what-to-say-aloud-while-demoing)

---

## What PreTerm is (one paragraph)

PreTerm is a **prediction-market workstation**: a single place to **watch binary contracts** (each shown as an **implied probability** that the “yes” outcome happens under the exchange’s rules), **read structured briefs** (what matters, what changed, bull/base/bear, catalysts, risks), **map headlines and feeds to the right contract**, **run sentiment on text or URLs or a subreddit’s hot page**, **research equities and SEC filings and macro indicators** beside that work, **save lists and whole desk layouts**, **plan real-world dates** with suggested contracts to watch, **tune alerts**, and **ask a Copilot** that is aware of your selected contract, pins, watchlists, and your last headline map.

---

## Vocabulary (read this first)

**Contract / market (in the UI)**  
A tradable binary question with a title, category, status, optional close time, and a price that PreTerm displays as **implied yes** (0–100%). This is **not** a claim that the world will turn out a certain way; it is the **market’s current consensus** shaped by participants and liquidity.

**Implied yes (shown as a big %)**  
The midpoint of “how the market prices a yes right now,” stored internally as a fraction and **rounded to a whole percent** almost everywhere in the UI.

**Points / pts (move)**  
**Percentage points** of implied yes, not “percent return.” Example: 61% to 64% is **+3 pts**, not “+3%.”

**Pin (to desk)**  
A **temporary focus flag** kept in the app while you work. Pinned contracts power the **Pinned** view on Monitor and feed **smart sort** and **Copilot**. Pins are **not** automatically saved to the server; see [Persistence](#what-is-saved-where-persistence).

**Watchlist**  
A **named, server-saved list** of contracts. Used for persistence, alert logic, and smart ordering when you enable it.

**Saved view**  
A **snapshot of your Monitor layout**: desk mode, category filter, search text, selected contract id, and pin list. Reopening a saved view **rehydrates** that working state and navigates you back into Monitor (optionally straight into a chosen contract).

**Desk mode (View)**  
- **All** — browse everything that passes filters.  
- **Pinned** — only contracts you pinned.  
- **Closing** — same filter set, but **sorted by soonest close time** (contracts without a date sort last).

**Smart sort**  
Optional reordering of the **All** or **Pinned** lists using **pins**, **watchlist membership**, and **recent detail opens** recorded in this browser. **Turns off** while **Closing** view is active, because closing order is authoritative.

**Event brief**  
Structured narrative blocks attached to a contract: summary, why now, what changed, drivers, catalysts, risks, scenario cases, “what would change probability,” optional curated headlines, and reference chips.

**Headline map**  
You paste or choose a headline; PreTerm suggests **which contract** the text is about and a **directional impact** label (e.g. whether the narrative is “good for yes” or “bad for yes” in a coarse sense—always interpret with judgment).

**Headline map session (for Copilot)**  
After a successful map, the app remembers the **headline text** and **full result** until replaced. Copilot can read that memory even if you navigate away from Headlines.

**Live wire**  
On Headlines, quick pulls of **Reddit hot** or **BBC World RSS** that populate clickable lines you can feed into mapping.

**Research desk**  
Standalone **equity quote + headlines + SEC** and **macro charts**—you do **not** have to pick a Kalshi contract first.

**Planner event**  
A dated real-world thing (wedding, trip, game, policy date, etc.) with a **concern type**; PreTerm suggests contracts that **overlap** with that concern in language and theme.

**Alerts / Notifications**  
Rules you configure in Settings can create **notification cards** you open from the header tray. You can **mark read** per item.

---

## What is saved where (persistence)

**On the server (survives new device, new browser, if you log in again)**  
- Your **account** (login).  
- **Watchlists** and their members.  
- **Saved views** (monitor snapshots).  
- **Planner events** and their stored suggestion payloads.  
- **Alert preferences** and **notification** history (as implemented).

**In this browser only (survives refresh, not a new device)**  
- Whether **smart sort** is turned on.  
- A **recent-opens history** used to bump contracts you looked at recently toward the top when smart sort is on.

**In memory for this tab session (lost on full reload unless captured in a Saved View)**  
- **Desk mode**, **category filter**, **search query**.  
- **Pinned market ids**.  
- **Selected market id** (what Monitor and Copilot treat as “selected”).  
- **Headline map session** (until you replace it or restart the SPA—provider is in-memory).

**Practical demo tip**  
If you **pin** contracts and want to **survive a refresh**, teach users to **Save Current Monitor Configuration** on Watchlists, or add important markets to a **watchlist** and rely on smart sort after reload.

---

## Routes you can land on

| URL | What it is |
|-----|------------|
| `/` | Redirects to `/app/monitor`. |
| `/login` | Sign-in screen (also used when auth is required). |
| `/register` | Create account. |
| `/app` | Redirects to `/app/monitor`. |
| `/app/monitor` | Contract grid (Monitor). |
| `/app/monitor/:id` | One contract, full detail. |
| `/app/watchlists` | Lists, quick add, saved views. |
| `/app/headlines` | Headline map + sentiment. |
| `/app/research` | Equities + macro. |
| `/app/planner` | Planner. |
| `/app/settings` | Profile snapshot + alerts. |
| Anything else unknown | Redirects to `/app/monitor`. |

---

## Boot and auth behavior

**“Loading PreTerm workspace…”**  
Full-screen message while auth state is **bootstrapping** (token check). Shown on **protected** routes and on **Login/Register** until bootstrap finishes.

**Protected `/app/*`**  
If not authenticated, you are sent to **Login** and the app **remembers which page you wanted** (e.g. Watchlists). After you sign in, it takes you **there** instead of the default Monitor.

**Login/Register while already signed in**  
Those pages use a **public-only** gate: if you are already authenticated, you are redirected to **`/app/monitor`** (you do not need to log in again).

---

## Sign in

**Page layout**  
Split **hero** (left) + **card** (right).

**Hero — eyebrow**  
“Desk Access”

**Hero — title**  
“PreTerm”

**Hero — body**  
“A prediction-market workstation for tracking live contracts, interpreting events, and keeping important decisions tied to the right market signals.”

**Hero — bullets**

1. “Monitor active contracts and save your desk state”
2. “Read event briefs, scenarios, and move timelines in one place”
3. “Map headlines and planning risks directly into relevant markets”

**Card — eyebrow**  
“Sign In”

**Card — title**  
“Open your desk”

**Card — subtitle**  
“Sign in with your account or use the prefilled demo credentials below.”

**Fields**

- **Email** — required. In many demos this arrives **prefilled** with the seeded demo address.
- **Password** — required. Often prefilled in demos.

**Primary action**

- **Sign In** — submits the form. Label becomes **“Signing In…”** and the button is **disabled** while the request runs.

**Failure**  
Red **form error** above the button with the server/message text (e.g. bad password).

**Footer**  
“Need an account? **Create one**” — navigates to Register.

**Success**  
Navigates to **Monitor** or back to the **page you originally tried to open**.

---

## Register

**Hero — eyebrow**  
“Registration”

**Hero — title**  
“Create your workspace”

**Hero — body**  
“Create an account to save watchlists, planner events, alert settings, and your preferred desk setup.”

**Card — eyebrow**  
“Create Account”

**Card — title**  
“Register for PreTerm”

**Card — subtitle**  
“Set up your account and start with a personalized prediction-market workspace.”

**Fields**

- **Display Name** — required.
- **Email** — required, email.
- **Password** — required, **minimum 8 characters**.

**Primary action**

- **Create Account** → **“Creating Account…”** while submitting; disabled during submit.

**Footer**  
“Already have an account? **Sign in**”

**Success**  
Goes to **`/app/monitor`**.

---

## The workstation shell (every authenticated page)

### Left rail — brand

- Square **“PT”** mark.
- Eyebrow: **“Prediction Market Workstation”**
- Product name: **“PreTerm”** (top-level heading in the rail).

### Left rail — identity card

- Kicker: **“Signed In”**
- **Bold display name**
- **Email** line.
- **Focus** line: shows your profile’s default focus label, or **“General desk”** if none is set.

### Left rail — navigation

Six **navigation links**. Each row:

- **Primary label** (larger)
- **Hint** (smaller)

Exact pairs:

1. **Monitor** — “Core workstation”
2. **Watchlists** — “Saved focus sets”
3. **Headlines** — “News mapping desk”
4. **Research** — “Stocks, SEC, macro”
5. **Planner** — “Hedge planning”
6. **Settings** — “Profile and preferences”

**Active route styling**  
The current page’s link is **visually highlighted**. When you drill into a contract at **`/app/monitor/123`**, the **Monitor** item **stays** highlighted so you know you are still in the Monitor “family.”

### Left rail — feed card

- Kicker: **“Feed”**
- Copy: **“Markets refresh on a timer when Kalshi is enabled. Pins stay in this browser session.”** (Meaning: live prices may update on a schedule; pin state is **session/workspace state**, not a server pin—pair this with [Persistence](#what-is-saved-where-persistence).)

### Top header — page meta

Changes by route:

| Route pattern | Eyebrow | Title | Subtitle |
|---------------|---------|-------|----------|
| `/app/monitor` (grid) | Primary Desk | Market Monitor | Track active contracts, inspect event briefs, and keep the main desk focused. |
| `/app/monitor/:id` | Contract | Market detail | Price history and Kalshi resolution context. |
| `/app/watchlists` | Personalization | Watchlists | Save the contracts and themes that deserve repeated attention. |
| `/app/headlines` | Event Mapping | Headlines Desk | Map events, inspect sentiment, and connect incoming news to the right market. |
| `/app/research` | Data | Research | Equity prices, SEC filings, and FRED macro series without tying to a Kalshi contract. |
| `/app/planner` | Risk Planning | Planner | Use markets as lightweight planning support for important real-world dates. |
| `/app/settings` | Account | Settings | Manage profile, desk defaults, alerts, and workspace preferences. |

### Top header — actions (right cluster)

1. **Alerts** button — ghost style; shows **pressed/active** styling when the tray is open. Label is **`Alerts`** or **`Alerts (N)`** when **N** unread notifications exist.

2. **Desk User** chip  
   - Small label **“Desk User”** + bold **display name** (duplicate of rail for at-a-glance).

3. **Log Out**  
   - Ghost button; clears auth and returns you to public flow.

### Notification tray (when Alerts is open)

**Panel header**

- Kicker **“Notifications”**
- Title **“Triggered alerts”**
- Small text: **`{unreadCount} unread`**

**Empty**  
“No triggered alerts yet. Add markets to watchlists and enable alert rules.”

**Each notification**

- **Title** (bold) + **timestamp** (locale-formatted).
- **Body** paragraph.
- If unread: **Mark Read** mini-button (per notification). Read items omit the button and use a **read** visual style on the card.

### Main + right column layout

- **Main** (wide): current page content.
- **Insight column** (narrow): **Copilot** on top, **User Context** card below.

**User Context card**

- Kicker **“User Context”**
- Bullets:
  - **Theme:** value or **“system”**
  - **Timezone:** value or **“Not set”**
  - **Headlines alerts:** **“Enabled”** or **“Off”** (from your saved preferences)

---

## Market Copilot (right column)

**Card header**

- Kicker **“Market Copilot”**
- Title **“Context-aware interpretation”**
- Small status: **“Market-linked”** if a selected contract detail is loaded, else **“Awaiting context”**

**Context chips**

- If nothing: a muted chip **“No active workstation context”**
- Otherwise one chip per line, for example:  
  - **Selected:** the contract title Copilot is anchored to.  
  - **Pinned:** how many contracts are pinned.  
  - **Watchlists:** how many watchlists you have loaded.  
  - **Headline map:** the title of the **top match** from your last successful map.

**Starter prompts (each is its own button chip)**

1. “Explain the selected market in plain market terms.”
2. “Summarize the bull, base, and bear cases.”
3. “What would need to happen for this market to move materially?”
4. “Compare this contract with the most related pinned market.”

Clicking any starter **sends it immediately** as a user message (same as typing and sending).

**Welcome message (initial assistant bubble)**  
“PreTerm Copilot is ready. I’ll use the selected market, pinned contracts, watchlists, and recent headline-map context when available.”  
Some replies may show a small **source** tag on the bubble (e.g. indicating a built-in fallback interpreter vs. an external model).

**Thread**

- **User** bubbles vs **Copilot** bubbles (different styling).
- Assistant bubbles can show a **small source** string under the name when present.
- While a reply is loading: assistant **loading** bubble: **“Analyzing current market context...”**

**Composer**

- **Textarea** placeholder: “Ask about the selected market, a mapped headline, or what would need to happen next.”
- **Send to Copilot** — primary button  
  - Disabled if draft **shorter than 2 characters**, or while sending, or **no auth token**.  
  - **“Thinking…”** while awaiting response.

**Errors**  
Red **form error** under the thread for failed requests.

**What “good context” looks like for demos**

- Open a contract detail **or** jump from Headlines so a contract is **selected** (Copilot loads the full brief in the background).
- Pin at least one other contract if you plan to ask **compare** questions.
- Run **Headline Map** once so the **Headline map:** chip appears.

---

## Monitor — contract grid

**Hero (compact panel)**

- Kicker **“Monitor”**
- Title **“Live contracts”**
- Lead: “Open any row for a full-page view with chart, timeline, and research panels. Pin contracts to narrow your desk.”

### Toolbar row (left to right)

**1. View — dropdown (“Desk view”)**  
Each option reads as **label — hint** in one line:

- **All —** Every contract matching your filters.  
- **Pinned —** Only markets you pinned on this desk.  
- **Closing —** Soonest resolution dates first.  

**2. Smart sort — checkbox + label**  
Label: **“Smart sort (recency & watchlists, this browser only)”**  
- Checked → reorder list using pins, watchlists, recent opens (see Vocabulary).  
- **Disabled** (and cannot be toggled) when **View = Closing**, because date sort wins.  
- Preference is **remembered in this browser** even across reloads.

**3. Category — dropdown**  
First choice is always **all**; below that, every **category label** that appears in the current feed (the list grows or shrinks with the data).

**4. Search**  
Label **“Search”**, placeholder **“Title or category”**.  
Filters to contracts whose **title** or **category** contains the query (case-insensitive). Empty query means **no text filter**.

### Flash message line

After some actions (e.g. quick **Watchlist** add on a card), a **flash message** bar can appear under the toolbar with human text like “{Market} added to {List}.”

### Universe header

- Kicker **“Universe”**
- Count heading: **`{n} contract`** or **`{n} contracts`**

### Error empty

**“Unable to load markets.”** — grid cannot populate.

### Pinned view empty

**“Nothing pinned yet. Use Pin on a contract (open it first) to build a focused list.”**  
Explains the prerequisite: open detail **or** use the card’s Pin control.

### Contract cards**Card body (large click target)**  
Whole card navigates to **`/app/monitor/{id}`**.

Inside the click area:

- **Title** (dominant type)
- Meta row: **category** + **status**
- **Horizontal meter** — fill width = implied yes % (purely visual glance aid)
- Stats row: big **%** + **signed pts** with positive/negative coloring

**Card footer actions**

- **Pin** / **Pinned** mini-button — toggles whether this contract is **on your pinned list** for this session.
- **Watchlist** mini-button — adds this contract to the **first watchlist** in your account (the first row returned). **Disabled** if you have **zero** watchlists (user must create one on Watchlists first).

---

## Monitor — contract detail

**Back control**

- Button **“← All markets”** → `/app/monitor` (grid).

**Loading**  
**“Loading contract…”**

**Error**  
**“This market could not be loaded. It may have been removed from the feed.”**

### Header

- Kicker **“Contract”**
- **Title** + **description** paragraph
- Stat grid:
  - **Implied** — whole-percent implied yes
  - **Move** — signed pts, colored positive/negative
  - **Volume** — thousands separators or **—**
- **Category badge**

### Actions row

- **Pin to desk** / **Pinned** — same toggle semantics as grid.
- Either:
  - **Add to {first watchlist name}** primary button, or  - Inline note: **“Create a watchlist to save this contract.”**

### Price history block

- Kicker **“Price history”**
- Subtitle **“Implied probability over recent sessions”**
- **Line chart** of snapshots (hover tooltip shows time + implied yes as **percent**). Y-axis is **zoomed** around the observed range so flat-looking high probabilities still show motion when points differ.

### Event Brief panel

See deep structure below (same component conceptually as anywhere else briefs appear).

**If no brief has been generated yet**  
Message: “There isn’t a generated brief for this contract in the database yet. It will appear after the next Kalshi refresh cycle.”

**When brief exists — top**

- Kicker **“Event Brief”**
- Repeated **contract title**
- **Summary** paragraph (under title)
- Scorecard:
  - **“Now”** kicker
  - Big **%** implied yes
  - Small line: signed **pts recent move** (“+N pts recent move” / “−N pts recent move”)

**Two-up context**

- **Why This Matters Now** — narrative paragraph
- **What Changed** — narrative paragraph

**Scenario toggle strip — three buttons**

- **Bull** — selects upside framing; applies **scenario-bull** tone class to frame- **Base** — base case; **scenario-base**
- **Bear** — downside; **scenario-bear**

Clicking **Bull**, **Base**, or **Bear** also jumps the **workbench** to the matching **case** section so the text always aligns with the scenario you picked.

**Scenario frame (large colored panel)**  
Shows scenario **title** and narrative:

| Mode | Panel kicker title |
|------|-------------------|
| Bull | Upside Framing |
| Base | Base Case |
| Bear | Downside Framing |

**Brief workbench — section navigator (7 buttons)**

Exact labels:

1. Drivers  
2. Bull Case  
3. Base Case  
4. Bear Case  
5. Catalysts  
6. Risks  
7. What Would Change This Probability  

Active button highlighted; body card shows matching field text.

**Move Timeline** (on detail, chart is separate so timeline stands alone)

- Kicker **“Move Timeline”**
- Empty: **“No move timeline is available yet.”**
- Each row: formatted **date/time**, **signed pts** chip, optional **linked label** (e.g. a headline tag), and **reason** copy.

**Recent Headlines**

- Kicker **“Recent Headlines”**
- Empty: **“No curated headlines are attached to this ticker yet. Use the Headlines desk to map wire copy to markets.”**
- Each item: **title**, **source · timestamp**, **why_it_matters** paragraph.

**Reference Inputs**

- Kicker **“Reference Inputs”**
- **Chips**: each chip names a **source type** and **label** (e.g. rules vs. market data).

> Note: The codebase also includes **Macro** and **Markets/SEC** context panels for embedding next to a contract when the UI wires them into this page; the shipped Monitor detail focuses on **chart + brief + timeline** as described above.

---

## Watchlists

**Hero**

- Kicker **“Persistence Layer”**
- Title **“Watchlists and saved views now personalize the desk.”**
- Body: capture monitor configuration, reopen later, attach contracts to named watchlists.

**Flash messages**  
Success/error strings from creates, adds, deletes (human-readable).

### Create Watchlist card

- Kicker **“Create Watchlist”**
- Title **“Named market baskets”**
- **Watchlist Name** text field, placeholder **“Macro Rotation Desk”**
- Submit: **“Create Watchlist”** (primary, form submit)

### Save Current View card

- Kicker **“Save Current View”**
- Title **“Persist monitor state”**
- **Saved View Name** field, placeholder **“Rates Focused Morning View”**
- Submit: **“Save Current Monitor Configuration”** (primary)

**What this captures (product explanation)**  
The saved view stores **desk mode**, **category**, **search**, **selected market id**, and **ordered pin list** from the Monitor context **at click time**. Teach users to set up the desk first, then save.

### Quick Add card

- Kicker **“Quick Add”**
- Title **“Current desk selection”**

Controls:

- **Target Watchlist** select — first option **“Select watchlist”** (empty value); then each list name.
- **Add Selected Market** — disabled if no list chosen or **no selected market** in Monitor context.
- **Add Pinned Markets (N)** — disabled if no list or **N=0** pins.

Read-only **meta list** mirrors Monitor context:

- Desk mode  
- Category filter  
- Search query or **“None”**  
- Selected market title or **“None”**

### Pinned Desk card

- Kicker **“Pinned Desk”**
- Title **“Currently pinned markets”**
- Empty: **“Pin markets from the monitor to surface them here.”**
- Else: mini cards with **title**, **category · %**

### Watchlists list section

- Kicker **“Watchlists”**
- Title **“{n} saved watchlists”**

Per watchlist **list card**:

- Header: **name**, **{m} markets**, **Delete** (ghost)
- Items: each row **title**, **category · %**, **Remove** mini-button
- If empty inner list: **“No markets yet.”**

### Saved Views section

- Kicker **“Saved Views”**
- Title **“{n} saved monitor states”**

Per view:

- **name**, subtitle **“{deskMode} desk”** (from saved filters)
- Buttons: **Open** (mini), **Delete** (mini)
- Meta bullets: **Category**, **Search**, **Pinned markets: {count}**

**Open** behavior

Replays filters + pins into Monitor and navigates to **`/app/monitor`** or **`/app/monitor/{id}`** if a selection id was stored.

---

## Headlines

**Hero**

- Kicker **“Headlines Desk”**
- Title **“Map events to markets and score narrative tone with market context.”**
- Body explains headline mapping, Reddit/BBC without API keys, VADER on text/URL/subreddit hot.

### Mode tabs (strip)

- **Headline Map** button-tab
- **Sentiment** button-tab

Active tab gets **active** styling (Map uses **scenario-base** accent; Sentiment **scenario-bull** accent in code).

---

### Mode: Headline Map

**Left — Input card**

- Kicker **“Input”**
- Title **“Headline to market”**

**Headline Text** — large text box, placeholder **“Paste a headline or event summary”**, about five lines tall.

**Sample chip row — four chips (each a button)**  
Clicking sets text **and** runs mapping:

1. “Cooler CPI print boosts odds of multiple Fed cuts this year”
2. “Spot bitcoin ETF inflows surge as BTC pushes toward fresh highs”
3. “Generic ballot shifts toward Democrats as suburban polling tightens”
4. “Hyperscaler capex commentary keeps Nvidia revenue expectations elevated”

**Live wire**

- Kicker **“Live wire”**
- **Subreddit** field (placeholder `worldnews`)
- **Reddit hot** — ghost; disabled while busy or if subreddit **&lt; 2** chars; shows **“Loading…”** while fetching
- **BBC World RSS** — ghost; disabled while busy
- Wire error in red when needed
- If results: bullet list where **each headline is a button** — sets textarea to that title and **runs map**

**Map error** — red box.

**Run Headline Map** — primary; disabled if headline **&lt; 8** chars or while running; **“Mapping Headline…”** state

**Right — Result card**

- Kicker **“Result”**
- Title **“Mapped market”**

Empty: **“Run a headline to see the top market match, directional impact, and deterministic explanation.”**

**Top match card**

- **Top Match** kicker + title
- **Directional impact** badge (class from impact string)
- Metrics: **Category**, **Match Strength** as whole percent
- Explanation paragraph
- **Why It Matters** block
- **Open Matched Market Brief** — primary; jumps to Monitor detail and sets selection

**Other candidates** (if more than one)

- Kicker **“Other Candidates”**
- Each candidate: full-row button with title, category · match %, impact badge → opens that market

**Side effect**  
Successful map stores **headline + full result** into **Headline Map context** for Copilot.

---

### Mode: Sentiment

**Left — Sentiment Input**

- Kicker **“Sentiment Input”**
- Title **“Text or URL to market tone”**

**Pasted Text** — textarea, placeholder **“Paste a headline, Reddit post text, or news excerpt”**, 6 rows.

**Sample chips — three buttons** (fill + run text sentiment):

1. “Bitcoin ETF inflows accelerated again and traders are leaning toward a breakout if macro liquidity stays supportive.”
2. “Multiple hot inflation components raise the risk that the Fed stays restrictive longer than the market expects.”
3. “Polling remains mixed, but the latest district-level movement looks slightly better for Democrats than last month.”

**Public URL** — single-line field, placeholder **“https://… (optional if you use Reddit hot below)”**

**Reddit without a thread URL**

- Kicker **“Reddit without a thread URL”**
- Note: explains server fetches public hot JSON, blends titles/selftext, scores bundle.
- **Subreddit** field (placeholder `worldnews`) — **same value as on the Headline Map tab** (switching tabs does not reset it)
- **Analyze subreddit hot** — primary; disabled if subreddit **&lt; 2** chars or while running; **“Analyzing…”**

**Sentiment error** — red

**Inline actions**

- **Analyze Text** — primary; disabled if text **&lt; 8** chars or busy; **“Analyzing...”**
- **Analyze URL** — ghost; disabled if URL **&lt; 10** chars or busy

**Right — Sentiment Output**

- Kicker **“Sentiment Output”**
- Title **“Market-relevant tone”**

Empty: **“Run sentiment analysis to see the VADER score, directional label, and matched market if the text is relevant.”**

**Result layout**

- **Analyzed Source** title + **sentiment label** badge
- Metrics: **Source** (human-readable name when available), **Compound Score** (three decimal places)
- Optional **Extraction Note** card (fetch problems, empty threads, etc.)
- **Related Market** card when present: title, why-it-matters, **Open Related Market Brief** button
- If no related market: **“No strong market match was found. Try more market-specific text or use the headline map tab.”**

---

## Research

**Hero**

- Kicker **“Research”**
- Title **“Equities (quotes, headlines, SEC) and macro”**
- Lead: Yahoo daily closes, EDGAR 10-K/10-Q/8-K under same ticker, FRED/API or CSV series—**no contract required**.

### Tab strip

- **Equities**
- **Macro (FRED)**

### Equities tab — controls

- **Ticker** text (forces uppercase as you type), default **AAPL**
- **Reddit sub (server fetch)** — you can type `r/stocks` or `stocks`; the app normalizes it; default **stocks**
- **Load quote & news** — primary; **“Loading…”** while quote loading
- **Load SEC filings** — ghost; **“EDGAR…”** while loading; uses **same ticker** as equities row
- **Refresh news only** — ghost; only appears after a **successful** quote; **“News…”** while refreshing

**Note**  
“Headlines use Google News RSS plus Reddit hot fetched through the API (avoids browser CORS on reddit.com).”

**Errors** — separate red lines: quote, EDGAR, equity news.

**Quote + chart region** (when quote available)

- **Quote** card: **name** heading, ticker, **Last:** price + currency, **exchange**
- **Recent daily closes** chart; empty inner: **“No history returned.”** Hover tooltip shows date + **Close**.

**Headlines card**

- Kicker **“Recent headlines”**
- Loading with no items yet: **“Loading headlines…”**
- Empty: **“No headlines yet. Load quote or refresh news.”**
- Each row: link opens **new tab** when URL exists; meta **source** + optional **score** label for Reddit-style scores

**SEC filings card** (when EDGAR payload available)

- Kicker **“SEC filings (EDGAR)”**
- Title: company name + **CIK**
- List items: **form** · **date** · **Open filing** link (new tab) · description line

### Macro tab

- **Series** dropdown — each row shows friendly **title** and short **key** in parentheses
- **Refresh** ghost — reloads series; disabled while **macroLoading**
- **“Loading series…”** when loading with no series object yet
- Series card: FRED kicker, **title**, id · frequency · units, **Latest:** value, line chart (tooltip date + value + units)

---

## Planner

**Hero**

- Kicker **“Planner”**
- Title **“Use markets as planning support, not just speculation.”**
- Body: add real-world event + concern → suggested contracts as **early-warning** or **decision-support** (not literal insurance).

### Left — New Planned Event

- Kicker **“New Planned Event”**
- Title **“Personal hedge planner”**

**Starter chips (two)**

1. **“Outdoor wedding weekend”** — fills date **2026-06-20**, location **Austin, TX**, concern **weather**, notes about weather/travel/inflation vendors.
2. **“Team offsite with investor update”** — **2026-09-15**, **New York, NY**, concern **business**, notes about rates/equities/company moves.

**Fields**

- **Event Title** — placeholder **“Outdoor wedding, trip, launch date, game day”**
- **Date** — date input
- **Location** — placeholder **“Chicago, IL”**
- **Concern Type** — select options:
  - Outdoor event / weather risk  
  - Trip / travel cost risk  
  - Game day / sports event  
  - Policy-sensitive date  
  - Business-sensitive date  
  - Crypto-sensitive date  
- **Notes** —5-row textarea, placeholder explains real-world risk to monitor through markets

**Create Planned Event** — primary; requires non-empty title + date; disabled while saving; **“Saving Plan…”**

### Right — Your Plans

- Kicker **“Your Plans”**
- Title **“Suggested monitoring markets”**

Empty: **“Create a planned event to see suggested contracts that can act as a decision-support layer.”**

**Each saved plan**

- Header: concern tag, title, **Remove** ghost button
- Metrics: **Date** (locale), **Location** or **“Not set”**
- Notes paragraph if present
- Suggestions empty: **“No strong market suggestions yet. Try more specific notes or a different concern type.”**

**Each suggestion row (button)**

- Title, category · **fit %** (relevance), rationale lines, badge with current implied **%**; click → Monitor detail + sets selection

---

## Settings

**Hero**

- Kicker **“Settings”**
- Title **“Profile and preference controls”**
- Intro: profile edits, desk defaults, alert preferences.

**Flash** line for load/save messaging.

### Account card

- Kicker **“Account”**
- Title = **display name**
- List: **Email**, **Timezone**, **Theme**

### Preferences card

- Kicker **“Preferences”**
- Title **“Desk Defaults”**
- List: **Categories:** count; **Desk mode:** preferred or **“Unassigned”**; **Move threshold:** value or **“No threshold configured”**

### Alert Rules card

- Kicker **“Alert Rules”**
- Title **“Watchlist-aware triggers”**

**Rule 1 — Market moved more than X%**

- Title + small copy: triggers when a **watched** market moves beyond threshold.
- **Numeric input** — default from saved rule or **5**; **on blur** writes threshold.
- Toggle button shows **“Enabled”** (primary) vs **“Enable”** (ghost) when off.

**Rule 2 — Watched market got a mapped headline**

- Copy mentions headline-linked context for a **watched** market.
- Toggle **Enabled** / **Enable** only.

**Rule 3 — Watched market entered a threshold range**

- Copy: crosses a **target probability level**.
- Number input — default **60** or saved; **on blur** saves.
- Toggle **Enabled** / **Enable**.

### Why These Matter card

Explains watchlists count, that rules pair with saved lists, notifications in tray, personalization story.

---

## Cross-desk workflows (storyboards)

**A. “News broke—what contract?”**  
Headlines → **Headline Map** → **Open Matched Market Brief** → read brief + timeline → optional **Pin** → **Watchlists** quick add.

**B. “I’m watching a basket”**  
Monitor: pin several names → **Watchlists** create list → **Add Pinned Markets** → enable **Smart sort** → verify ordering.

**C. “Restore Monday morning layout”**  
Set category + search + pins → **Watchlists** **Save Current Monitor Configuration** → later **Open** that saved view.

**D. “Is this paragraph bullish?”**  
Headlines → **Sentiment** → paste text → **Analyze Text** → if related market appears, open brief.

**E. “What’s NVDA filing?”**  
Research → ticker **NVDA** → **Load quote & news** → **Load SEC filings** → open links.

**F. “Wedding weather anxiety”**  
Planner → starter chip or custom → **Create** → click suggested macro/weather-adjacent contract → Monitor detail.

**G. “Explain like I’m busy”**  
Select contract + run headline map → Copilot starter **Explain the selected market** or **Summarize bull/base/bear**.

---

## Validation and disabled rules (quick matrix)

| Location | Rule |
|----------|------|
| Headline Map — run | Headline **≥8** chars |
| Headline Map — Reddit hot | Subreddit **≥ 2** chars; disabled while the live wire is loading |
| Sentiment — text | **≥ 8** chars |
| Sentiment — URL | **≥ 10** chars |
| Sentiment — Reddit hot | Subreddit **≥ 2** chars; disabled while a sentiment run is in flight |
| Copilot — send | Draft **≥ 2** chars; needs token; not while sending |
| Copilot — starter | Disabled while a reply is loading |
| Watchlists — add selected | Needs target list + selected market |
| Watchlists — add pinned | Needs target list + ≥1 pin |
| Planner — create | Non-empty title + date |
| Research — EDGAR | Non-empty ticker (trimmed) |

---

## Empty states and system messages (catalog)

| Surface | Message |
|---------|---------|
| Monitor grid | “Unable to load markets.” |
| Monitor pinned | “Nothing pinned yet…” |
| Contract detail load | “Loading contract…” / removal error (see detail section) |
| Brief missing | “There isn’t a generated brief…” |
| Timeline missing | “No move timeline is available yet.” |
| Brief headlines missing | “No curated headlines…” |
| Notifications | “No triggered alerts yet…” |
| Headlines map result | “Run a headline to see…” |
| Sentiment result | “Run sentiment analysis to see…” |
| Sentiment no market | “No strong market match…” |
| Research headlines | “No headlines yet…” |
| Research chart | “No history returned.” |
| Planner plans | “Create a planned event…” |
| Planner suggestions | “No strong market suggestions yet…” |
| Watchlists pinned card | “Pin markets from the monitor…” |
| Watchlist inner | “No markets yet.” |
| Copilot context | “No active workstation context” |

---

## Visual language (what colors and badges mean)

**Delta / move coloring**  
Positive and negative **pts** use **green/red (or equivalent) styling** for quick scanning—**not** investment advice, just **direction of repricing**.

**Scenario tones**  
Bull/Base/Bear toggles map to **scenario-bull**, **scenario-base**, **scenario-bear** accents on the scenario frame—visual **framing**, not a forecast.

**Impact / sentiment badges**  
Headline **directional_impact** and sentiment **label** render as badge components; treat them as **coarse labels** that deserve human review.

**Meter bar on cards**  
Horizontal fill = implied yes %—a **glanceable** anchor before opening detail.

---

## Personas — “a day in the life”

**Policy researcher**  
Starts in **Monitor** (Closing) → opens fiscal/policy contracts → **Headline Map** on breaking news → **Copilot** summarizes → saves **Saved View** “Budget week.”

**Retail investor (informational)**  
**Research** for equity + SEC → **Headlines Sentiment** on Fed story → **Headline Map** to related macro contract → pins one ticker for the week.

**Event planner**  
**Planner** for outdoor wedding → reads suggested contracts as **conversation starters** with finance-savvy family, not as purchases.

**Instructor**  
Uses **samples** everywhere to teach **implied probability** vs headlines; shows **pts** moves after refresh cycles.

---

## Extended demo script (step-by-step)

1. Open app; observe redirect to Monitor if logged in.  
2. If not, hit `/app/watchlists`—note redirect to Login with **return** path.  
3. Login; confirm you land on intended page.  
4. Read **rail** identity + six nav hints.  
5. **Monitor**: read hero.  
6. Toggle **View** through All → Pinned (see empty if no pins) → Closing.  
7. Set **Category** to a non-all value; reset to all.  
8. Type partial **Search**; clear it.  
9. Enable **Smart sort**; disable; re-enable.  
10. Switch to **Closing**; confirm smart sort checkbox **disabled**.  
11. Open a **card** (main click).  
12. On detail: read **Implied / Move / Volume**.  
13. **Pin**; go back; switch **Pinned** view; see card present.  
14. Return to detail; **Unpin** from header.  
15. If watchlist exists: **Add to …**; read flash on grid if you repeat from card **Watchlist** button.  
16. Study **Price history** tooltip.  
17. Scroll **Event Brief**: read summary + scorecard.  
18. Click **Bull**, then **Bear**, then **Base**; watch frame.  
19. Click every **workbench** section tab; read copy.  
20. Scroll **Move Timeline** rows.  
21. Open **Headlines**; **Headline Map** tab.  
22. Click **sample chip 1**; wait for result.  
23. Read **Match Strength** + **Why It Matters**.  
24. **Open Matched Market Brief**.  
25. Open **Copilot**; click **Summarize bull, base, and bear**.  
26. Return **Headlines** → **Live wire** → **BBC World RSS**; click a line to remap.  
27. Switch **Sentiment** tab; run **sample** text chip.  
28. Paste a **short** URL; try **Analyze URL**.  
29. Run **Analyze subreddit hot** on `worldnews`.  
30. **Research** → **Equities**; **Load quote & news** on `AAPL`.  
31. Hover chart; open a headline link (new tab).  
32. **Load SEC filings**; open an **Open filing** link.  
33. **Refresh news only**.  
34. Switch **Macro**; change **Series**; hit **Refresh**.  
35. **Watchlists**: create list; **Quick Add** selected market (set selection via Monitor first).  
36. **Save Current View** with a memorable name.  
37. Change Monitor filters; **Open** saved view; confirm restoration.  
38. **Planner**: use starter chip; **Create**; click a suggestion.  
39. **Settings**: nudge threshold inputs; toggle a rule **off** then **on**.  
40. Open **Alerts** tray; **Mark Read** if items exist.  
41. **Log Out**; confirm Login accessible again.

---

## FAQ (user confusion)

**Why did my pins disappear?**  
Pins live in **session state**. Use a **Saved View** or **watchlists** for durability across reloads.

**Why is Watchlist disabled on the card?**  
You have **zero** watchlists—create one first.

**Why does Copilot say it needs context?**  
**Select** a contract (open detail or jump from Headlines) so the right column loads **Market-linked** context.

**“Match strength” isn’t 100%—is the map wrong?**  
Strength is a **relative** score for ranking; always read **explanation** + **why it matters**.

**Why two different Reddit subreddit boxes on Headlines?**  
They share one **subreddit state**—changing it in Map mode affects Sentiment mode and vice versa.

**Is Research tied to my Kalshi contract?**  
No—Research is intentionally **standalone** for equity/macro homework.

---

## Appendix — sample content shipped in the UI

**Headline Map samples**  
See the **four sample chips** under [Headlines — Headline Map](#mode-headline-map).

**Sentiment samples**  
See the **three sample chips** under [Headlines — Sentiment](#mode-sentiment).

**Planner starters**  
Outdoor wedding weekend; Team offsite with investor update (with their default fields).

**Copilot starters**  
Four strings in § Copilot.

**Register password rule**  
Minimum **8** characters.

---

---

## Reading order (how to scan each screen without getting lost)

**Monitor grid**  
Start at the **hero** sentence (what this page is for). Glance **View** (are you in All, Pinned, or Closing?). Check **Smart sort** (on/off). Then **Category** and **Search** (are you accidentally narrowed?). Read the **Universe count** so you know if filters zeroed you out. Scan cards **top-to-bottom, left-to-right**: title → category/status → meter → % → pts → Pin/Watchlist.

**Monitor detail**  
**Back** if wrong contract. Read **title + description** (what question is this?). Read **Implied / Move / Volume** as a triad: level, recent repricing, activity. **Pin / Watchlist** if you want persistence. **Chart** next (shape of belief). Then **Event Brief** top summary + scorecard. Read **Why now** and **What changed** as the “executive summary.” Pick **Bull/Base/Bear** once for framing, then use the **workbench tabs** for depth. Finish with **Timeline** (sequence story) and **Headlines** / **Reference** if present.

**Watchlists**  
Top: create vs save. Middle: **Quick Add** only makes sense after you understand **selected** vs **pinned** (read the meta list). Bottom: expand each watchlist to see members; expand saved views to see **Open** vs **Delete**.

**Headlines**  
Pick **mode** first. In **Map**, work **Input → Live wire (optional) → Run**. In **Sentiment**, decide **text vs URL vs subreddit**—they are three different “shapes” of input.

**Research**  
Pick **Equities vs Macro** first. Equities path is **Ticker → Load** → read quote → chart → scroll headlines → optionally SEC. Macro path is **Series → watch chart refresh**.

**Planner**  
Read **starter chips** as examples, not prescriptions. Fill **title + date** minimally, then enrich with **concern + notes** to improve suggestions. On the right, read each plan **top to bottom**, then each **suggestion button** as a “candidate hedge / indicator.”

**Settings**  
Account snapshot first (identity). Preferences second (defaults). Rules third—each rule is **read the title + small explainer**, then **number**, then **Enable** state.

---

## Worked example — reading one card in English

Imagine a card shows **61%**, **+3 pts**, category **macro**, status **open**.

- **61%** — participants currently price “yes” a little above half; interpret only with the **title** and rules.  
- **+3 pts** — since the prior reference update, the market moved **three percentage points** toward “yes.” That is a **repricing**, not “made3% profit.”  
- **macro** — thematic bucket for filtering and mental model.  
- **open** — still tradable / active in the feed (wording comes from the data source).  
- **Meter** — same 61% as length so your eye catches extremes vs. coin flip.  
- **Pin** — “I want this in my short list.”  
- **Watchlist** — “Save this into my named basket (first list).”

---

## Narration cues (what to say aloud while demoing)

- On **Login:** “This is intentionally boring—we get you to the desk fast; demo credentials are prefilled.”  
- On **Monitor View:** “All is my Bloomberg terminal wide shot; Pinned is my working set; Closing is my calendar sort.”  
- On **Smart sort:** “This is personal prioritization—it boosts things I opened recently and things already in my watchlists.”  
- On **Headline Map:** “This is not magic NLP—it’s a structured matcher with explanations you can challenge.”  
- On **Sentiment:** “Think tone meter for pasted text; related market is best-effort.”  
- On **Research:** “This desk is for when the story is bigger than one Kalshi line—equities filings macro in one place.”  
- On **Planner:** “We’re not selling insurance—we’re surfacing contracts that speak the same language as your real-world risk.”  
- On **Copilot:** “This is narration on top of *your* context, not generic chat.”

---

## Maintainer note

When you add a **button, tab, or empty state**, update this document in the same change so it remains a **complete product inventory**, not marketing fluff.
