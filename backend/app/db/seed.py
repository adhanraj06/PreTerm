import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import AlertPreference
from app.core.config import settings
from app.core.security import hash_password
from app.models.market import Market, MarketBrief, MarketSnapshot, MarketTimelineEntry
from app.models.user import User, UserPreference, UserProfile


def _dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _generate_timeline_entries(record: dict[str, object]) -> list[dict[str, object]]:
    explicit_entries = record.get("timeline_entries")
    if isinstance(explicit_entries, list):
        return explicit_entries

    snapshots = record.get("snapshots", [])
    brief = record.get("brief")
    generated: list[dict[str, object]] = []
    if not isinstance(snapshots, list) or len(snapshots) < 2:
        return generated

    recent_headlines: list[dict[str, object]] = []
    if isinstance(brief, dict):
        recent = brief.get("recent_headlines")
        if isinstance(recent, list):
            recent_headlines = recent

    for index in range(1, len(snapshots)):
        current = snapshots[index]
        previous = snapshots[index - 1]
        move = round(current["price"] - previous["price"], 4)
        linked = recent_headlines[min(index - 1, len(recent_headlines) - 1)] if recent_headlines else None
        generated.append(
            {
                "occurred_at": current["captured_at"],
                "move": move,
                "price_after_move": current["price"],
                "reason": linked.get("why_it_matters")
                if isinstance(linked, dict) and linked.get("why_it_matters")
                else (
                    brief.get("what_changed")
                    if isinstance(brief, dict) and brief.get("what_changed")
                    else "Seeded price move tied to evolving market context."
                ),
                "linked_label": linked.get("title")
                if isinstance(linked, dict)
                else None,
                "linked_type": "headline" if isinstance(linked, dict) else "context",
                "linked_url": None,
                "metadata_json": {
                    "kind": "move",
                    "source": record.get("source", "seed"),
                },
            }
        )
    return generated


SEED_MARKETS: list[dict[str, object]] = [
    {
        "external_id": "macro-fed-cuts-2026",
        "source": "seed",
        "title": "Will the Fed deliver at least two rate cuts by September 2026?",
        "slug": "fed-two-cuts-by-september-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-09-18T19:00:00Z",
        "last_price": 0.61,
        "probability_change": 0.04,
        "volume": 284000,
        "open_interest": 193000,
        "description": "A macro contract tracking whether the Federal Reserve eases policy at least twice by its September 2026 meeting.",
        "metadata_json": {
            "desk": "rates",
            "tags": ["fed", "rates", "inflation"],
            "resolution_criteria": "Resolves yes if cumulative target-rate cuts reach 50 bps or more by the September 2026 meeting.",
        },
        "brief": {
            "summary": "The market is leaning toward a moderate easing path after inflation cooled from prior highs but labor data remained resilient.",
            "why_this_matters_now": "Rates expectations influence equities, duration-sensitive assets, and recession pricing across the entire workstation.",
            "what_changed": "The contract moved higher after softer inflation prints and a mild downside surprise in activity indicators reduced the urgency of a higher-for-longer stance.",
            "bull_case": "Disinflation persists, hiring slows, and the Fed feels comfortable delivering two insurance cuts before growth weakens materially.",
            "base_case": "The Fed cuts once early enough to stabilize conditions, then waits for more evidence before committing to a second move.",
            "bear_case": "Sticky services inflation or a reacceleration in wages forces the Fed to stay restrictive longer than the market now expects.",
            "catalysts": "CPI, PCE, payrolls, FOMC communications, Treasury auction demand.",
            "drivers": "Core inflation trend, labor slack, financial conditions, real yields.",
            "risks": "A one-off inflation shock or geopolitical commodity spike could reverse the move quickly.",
            "what_would_change_probability": "Two consecutive hot inflation reports or a materially stronger payroll sequence would reduce cut probability. A weak employment trend would raise it.",
            "sources_json": [
                {"label": "FOMC statement", "type": "policy"},
                {"label": "CPI release", "type": "macro"},
                {"label": "PCE inflation", "type": "macro"},
            ],
            "recent_headlines": [
                {
                    "title": "Treasury yields slide after cooler inflation reading",
                    "source": "Desk Wire",
                    "published_at": "2026-04-17T14:10:00Z",
                    "why_it_matters": "Lower yields improved confidence that the Fed can cut twice without a fresh inflation scare.",
                },
                {
                    "title": "Fed officials signal patience but acknowledge softer demand",
                    "source": "Macro Journal",
                    "published_at": "2026-04-16T19:30:00Z",
                    "why_it_matters": "Balanced messaging kept the market centered on incoming labor and inflation data rather than hawkish rhetoric alone.",
                },
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.56, "volume": 250000, "open_interest": 175000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.59, "volume": 268000, "open_interest": 184000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.61, "volume": 284000, "open_interest": 193000},
        ],
    },
    {
        "external_id": "macro-us-recession-2026",
        "source": "seed",
        "title": "Will the U.S. enter recession by Q4 2026?",
        "slug": "us-recession-by-q4-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-12-31T22:00:00Z",
        "last_price": 0.37,
        "probability_change": -0.03,
        "volume": 211000,
        "open_interest": 149000,
        "description": "A macro market expressing the probability of an NBER-style recession call before the end of 2026.",
        "metadata_json": {"desk": "growth", "tags": ["recession", "macro", "labor"]},
        "brief": {
            "summary": "Recession odds eased as growth stabilized, but the market still assigns meaningful downside risk from lagged tightening and fragile consumer momentum.",
            "why_this_matters_now": "This contract acts as a portfolio-level regime signal for risk assets and informs how defensive the user’s desk should become.",
            "what_changed": "Probability drifted lower after stronger retail spending and less-bad survey data challenged the immediate hard-landing narrative.",
            "bull_case": "Household balance sheets hold up, policy eases enough to support demand, and growth merely slows rather than contracts.",
            "base_case": "A below-trend economy persists with rolling weakness but avoids a formal recession call in the resolution window.",
            "bear_case": "Labor softening accelerates, credit conditions tighten, and business spending pulls back hard enough to tip the economy into recession.",
            "catalysts": "Payrolls, ISM surveys, credit spreads, consumer confidence, loan officer surveys.",
            "drivers": "Employment trend, consumption resilience, commercial credit stress, Fed stance.",
            "risks": "This market can move sharply on sentiment data even when hard data remain mixed.",
            "what_would_change_probability": "Sustained jobless claims deterioration and broad PMIs below contraction thresholds would push odds higher. Strong payrolls would push them lower.",
            "sources_json": [
                {"label": "NBER business cycle framework", "type": "reference"},
                {"label": "ISM Manufacturing", "type": "macro"},
            ],
            "recent_headlines": [
                {
                    "title": "Retail sales stabilize as consumers keep spending on services",
                    "source": "Macro Journal",
                    "published_at": "2026-04-17T12:45:00Z",
                    "why_it_matters": "Hard-landing fears eased after a firmer demand read.",
                },
                {
                    "title": "Credit strategists warn lower-quality borrowers are still under pressure",
                    "source": "Desk Wire",
                    "published_at": "2026-04-15T15:20:00Z",
                    "why_it_matters": "The downside recession case remains live even as near-term data improved.",
                },
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.41, "volume": 190000, "open_interest": 142000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.39, "volume": 201000, "open_interest": 146000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.37, "volume": 211000, "open_interest": 149000},
        ],
    },
    {
        "external_id": "macro-core-cpi-sub-3",
        "source": "seed",
        "title": "Will U.S. core CPI fall below 3.0% year-over-year by August 2026?",
        "slug": "core-cpi-below-3-by-august-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-08-15T14:00:00Z",
        "last_price": 0.68,
        "probability_change": 0.05,
        "volume": 177000,
        "open_interest": 121000,
        "description": "Tracks the probability that core CPI prints with a 2-handle before late summer 2026.",
        "metadata_json": {"desk": "inflation", "tags": ["cpi", "disinflation", "macro"]},
        "brief": {
            "summary": "The market increasingly expects inflation normalization to continue, though shelter and services remain the key holdouts.",
            "why_this_matters_now": "This is a direct input into rate-cut probability and one of the cleanest macro-to-market causal chains in the product.",
            "what_changed": "Odds increased as several monthly inflation components softened simultaneously instead of relying on one-off categories.",
            "bull_case": "Shelter disinflation broadens and wage pressure moderates enough to drag core CPI through the 3% threshold.",
            "base_case": "Inflation trends lower but lands just around 3%, keeping the market close to a coin flip late in the cycle.",
            "bear_case": "Services inflation proves sticky and keeps core CPI above target-friendly levels even if goods remain benign.",
            "catalysts": "Monthly CPI, owners' equivalent rent trend, average hourly earnings, import prices.",
            "drivers": "Shelter lag, labor costs, goods normalization, healthcare and insurance components.",
            "risks": "Methodology or seasonal quirks can create noisy short-term moves without changing the broader trend.",
            "what_would_change_probability": "A sustained shelter rollover would lift odds further. Sticky supercore inflation would reduce them.",
            "sources_json": [{"label": "BLS CPI release", "type": "macro"}],
            "recent_headlines": [
                {
                    "title": "Shelter disinflation broadens in latest monthly CPI release",
                    "source": "Inflation Monitor",
                    "published_at": "2026-04-17T13:05:00Z",
                    "why_it_matters": "The market moved higher because the sticky component finally showed broader cooling.",
                }
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.62, "volume": 154000, "open_interest": 109000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.65, "volume": 166000, "open_interest": 116000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.68, "volume": 177000, "open_interest": 121000},
        ],
    },
    {
        "external_id": "politics-house-2026-dem",
        "source": "seed",
        "title": "Will Democrats win the U.S. House in 2026?",
        "slug": "democrats-win-house-2026",
        "category": "politics",
        "status": "open",
        "close_time": "2026-11-04T05:00:00Z",
        "last_price": 0.57,
        "probability_change": 0.02,
        "volume": 342000,
        "open_interest": 251000,
        "description": "Election market tied to party control of the U.S. House after the 2026 cycle.",
        "metadata_json": {"desk": "elections", "tags": ["house", "midterms", "politics"]},
        "brief": {
            "summary": "The House control market sits in a narrow but meaningful Democratic lead as the usual midterm pattern competes with district-level incumbency and redistricting effects.",
            "why_this_matters_now": "This is a flagship politics contract that anchors the demo’s event interpretation and scenario engine flows.",
            "what_changed": "The contract firmed after early generic-ballot movement and a less favorable incumbent environment for the governing coalition.",
            "bull_case": "The opposition benefits from the normal midterm penalty, candidate quality holds, and suburban seats swing enough to flip control.",
            "base_case": "The race remains close and seat-level execution matters more than national mood alone.",
            "bear_case": "Economic stabilization and stronger approval data blunt the midterm effect, keeping the majority intact.",
            "catalysts": "Generic ballot updates, fundraising reports, special elections, approval tracking.",
            "drivers": "National mood, district candidate quality, turnout composition, issue salience.",
            "risks": "Early-cycle polling can create false confidence before the candidate map is settled.",
            "what_would_change_probability": "A consistent widening in the generic ballot or weak approval readings would push odds higher. A stabilizing incumbent environment would cut them.",
            "sources_json": [
                {"label": "Generic ballot polling average", "type": "polling"},
                {"label": "FEC filings", "type": "campaign"},
            ],
            "recent_headlines": [
                {
                    "title": "Generic ballot edges toward opposition as suburban seats tighten",
                    "source": "Election Desk",
                    "published_at": "2026-04-17T16:25:00Z",
                    "why_it_matters": "The market’s recent bid is tied to marginal district deterioration rather than a full national wave.",
                },
                {
                    "title": "Early fundraising reports show stronger challenger recruitment",
                    "source": "Campaign Ledger",
                    "published_at": "2026-04-16T18:10:00Z",
                    "why_it_matters": "Candidate quality is reinforcing the favorable directional setup for a House flip.",
                },
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.53, "volume": 301000, "open_interest": 230000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.55, "volume": 321000, "open_interest": 241000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.57, "volume": 342000, "open_interest": 251000},
        ],
    },
    {
        "external_id": "politics-senate-2026-gop",
        "source": "seed",
        "title": "Will Republicans control the Senate after the 2026 election?",
        "slug": "republicans-control-senate-2026",
        "category": "politics",
        "status": "open",
        "close_time": "2026-11-04T05:00:00Z",
        "last_price": 0.63,
        "probability_change": -0.01,
        "volume": 296000,
        "open_interest": 219000,
        "description": "Election contract on party control of the U.S. Senate after the 2026 cycle.",
        "metadata_json": {"desk": "elections", "tags": ["senate", "midterms", "politics"]},
        "brief": {
            "summary": "Senate control still leans Republican because the map remains structurally favorable, though the market has trimmed some confidence.",
            "why_this_matters_now": "The Senate market complements the House contract and produces richer split-government scenarios for the product.",
            "what_changed": "Odds softened slightly as candidate recruitment improved for key battleground races and local polling tightened.",
            "bull_case": "The defensive map remains too difficult for the opposition, and incumbency plus fundraising protect the majority.",
            "base_case": "The chamber is decided by a handful of races and remains modestly tilted by structural map advantage.",
            "bear_case": "Poor candidate quality or a sharply worsening national environment flips enough battleground seats to lose control.",
            "catalysts": "Candidate announcements, fundraising, local polling, approval trends.",
            "drivers": "State partisanship, incumbency, turnout mix, national wave risk.",
            "risks": "Thin polling in certain states can exaggerate short-term contract moves.",
            "what_would_change_probability": "High-quality opposition candidates in key states would lower odds. A favorable national swing would also matter materially.",
            "sources_json": [{"label": "State polling", "type": "polling"}],
            "recent_headlines": [
                {
                    "title": "Recruitment improves in two key Senate battlegrounds",
                    "source": "Election Desk",
                    "published_at": "2026-04-16T17:20:00Z",
                    "why_it_matters": "The structurally favorable map still leans one way, but candidate quality narrowed the spread.",
                }
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.65, "volume": 281000, "open_interest": 214000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.64, "volume": 289000, "open_interest": 217000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.63, "volume": 296000, "open_interest": 219000},
        ],
    },
    {
        "external_id": "politics-pres-approval-50",
        "source": "seed",
        "title": "Will presidential approval exceed 50% by July 2026?",
        "slug": "presidential-approval-over-50-by-july-2026",
        "category": "politics",
        "status": "open",
        "close_time": "2026-07-31T23:00:00Z",
        "last_price": 0.34,
        "probability_change": 0.03,
        "volume": 128000,
        "open_interest": 81000,
        "description": "Tracks whether a national approval average clears 50% before August 2026.",
        "metadata_json": {"desk": "approval", "tags": ["approval", "politics"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.29, "volume": 112000, "open_interest": 76000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.31, "volume": 119000, "open_interest": 79000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.34, "volume": 128000, "open_interest": 81000},
        ],
    },
    {
        "external_id": "crypto-btc-ath-2026",
        "source": "seed",
        "title": "Will Bitcoin make a new all-time high by December 2026?",
        "slug": "bitcoin-new-all-time-high-by-december-2026",
        "category": "crypto",
        "status": "open",
        "close_time": "2026-12-31T23:59:00Z",
        "last_price": 0.58,
        "probability_change": 0.06,
        "volume": 411000,
        "open_interest": 322000,
        "description": "Directional crypto market on whether Bitcoin prints a new cycle high before year-end 2026.",
        "metadata_json": {"desk": "crypto", "tags": ["bitcoin", "ath", "risk-assets"]},
        "brief": {
            "summary": "Bitcoin ATH odds remain constructive as liquidity conditions improve and institutional demand remains the dominant narrative.",
            "why_this_matters_now": "This is the flagship crypto contract and a high-signal proxy for broader speculative risk appetite.",
            "what_changed": "The market repriced higher after a strong breakout attempt and renewed ETF-related flows into the asset complex.",
            "bull_case": "Macro conditions ease, ETF demand persists, and a limited spot float amplifies upside through momentum-driven positioning.",
            "base_case": "Bitcoin trends higher but needs one more macro tailwind or sentiment catalyst to decisively break prior highs.",
            "bear_case": "Risk sentiment fades, regulatory overhang returns, or mining/holder supply caps rallies below prior peaks.",
            "catalysts": "ETF flows, macro liquidity, crypto regulation headlines, large holder positioning.",
            "drivers": "Dollar trend, real yields, institutional demand, leverage in perpetual futures.",
            "risks": "Crypto contracts can gap violently on weekend headlines and exchange-specific stress.",
            "what_would_change_probability": "A sustained breakout with strong spot participation would increase odds. Higher real yields or regulatory stress would cut them.",
            "sources_json": [
                {"label": "Spot ETF flow trackers", "type": "crypto"},
                {"label": "BTC price action", "type": "market"},
            ],
            "recent_headlines": [
                {
                    "title": "Spot bitcoin funds see strongest weekly inflow streak in months",
                    "source": "Crypto Flow Daily",
                    "published_at": "2026-04-17T11:00:00Z",
                    "why_it_matters": "The contract repriced higher because institutional demand is supporting breakout attempts.",
                },
                {
                    "title": "Dollar softness boosts crypto beta across majors",
                    "source": "Digital Assets Brief",
                    "published_at": "2026-04-16T21:00:00Z",
                    "why_it_matters": "Macro liquidity conditions are reinforcing the upside scenario instead of fighting it.",
                },
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.49, "volume": 370000, "open_interest": 291000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.54, "volume": 392000, "open_interest": 307000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.58, "volume": 411000, "open_interest": 322000},
        ],
    },
    {
        "external_id": "crypto-eth-etf-flows",
        "source": "seed",
        "title": "Will net spot ETH ETF flows be positive in Q3 2026?",
        "slug": "spot-eth-etf-flows-positive-q3-2026",
        "category": "crypto",
        "status": "open",
        "close_time": "2026-09-30T23:00:00Z",
        "last_price": 0.52,
        "probability_change": 0.01,
        "volume": 167000,
        "open_interest": 119000,
        "description": "Crypto market on whether aggregate net spot ETH ETF flows finish Q3 2026 positive.",
        "metadata_json": {"desk": "crypto", "tags": ["ethereum", "etf", "flows"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.50, "volume": 153000, "open_interest": 113000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.51, "volume": 161000, "open_interest": 116000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.52, "volume": 167000, "open_interest": 119000},
        ],
    },
    {
        "external_id": "crypto-sol-200",
        "source": "seed",
        "title": "Will SOL trade above $200 before October 2026?",
        "slug": "sol-above-200-before-october-2026",
        "category": "crypto",
        "status": "open",
        "close_time": "2026-10-01T00:00:00Z",
        "last_price": 0.44,
        "probability_change": -0.02,
        "volume": 141000,
        "open_interest": 92000,
        "description": "Alt-asset momentum contract tied to SOL reclaiming a major psychological price level.",
        "metadata_json": {"desk": "crypto", "tags": ["solana", "alts", "momentum"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.47, "volume": 133000, "open_interest": 88000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.45, "volume": 137000, "open_interest": 90000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.44, "volume": 141000, "open_interest": 92000},
        ],
    },
    {
        "external_id": "equities-spx-6000",
        "source": "seed",
        "title": "Will the S&P 500 close above 6,000 by August 2026?",
        "slug": "sp500-close-above-6000-by-august-2026",
        "category": "equities",
        "status": "open",
        "close_time": "2026-08-31T21:00:00Z",
        "last_price": 0.55,
        "probability_change": 0.03,
        "volume": 256000,
        "open_interest": 178000,
        "description": "Broad equities market on whether the S&P 500 prints a 6,000+ closing level by the end of August 2026.",
        "metadata_json": {"desk": "equities", "tags": ["spx", "index", "risk-on"]},
        "brief": {
            "summary": "The S&P contract sits modestly above even odds as easing-rate expectations and AI-linked earnings optimism offset concerns about stretched positioning.",
            "why_this_matters_now": "This is the cleanest broad risk-on benchmark in the equity sleeve and ties directly into macro and tech narratives elsewhere in the app.",
            "what_changed": "Probability rose after a broad-based rally led by mega-cap growth and improving breadth outside the most crowded names.",
            "bull_case": "Earnings remain firm, rates ease just enough, and investors keep paying up for growth plus resilience.",
            "base_case": "The index trades choppy but drifts higher, leaving a late-window test of 6,000 plausible rather than certain.",
            "bear_case": "Valuation compression or a growth scare drags the index lower before it can reach the target.",
            "catalysts": "CPI, payrolls, earnings season, Treasury yields, large-cap guidance.",
            "drivers": "Multiple expansion, earnings breadth, real yields, positioning.",
            "risks": "Crowded long positioning makes the contract vulnerable to abrupt derisking on seemingly minor macro surprises.",
            "what_would_change_probability": "A drop in yields with stable earnings would raise odds. Margin pressure or weak forward guidance would reduce them.",
            "sources_json": [
                {"label": "S&P 500 price action", "type": "market"},
                {"label": "Large-cap earnings reports", "type": "earnings"},
            ],
            "recent_headlines": [
                {
                    "title": "Mega-cap earnings optimism pushes index breadth wider",
                    "source": "Equity Tape",
                    "published_at": "2026-04-17T15:40:00Z",
                    "why_it_matters": "Broader participation made the 6,000 path look more credible than a narrow momentum squeeze.",
                }
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.50, "volume": 231000, "open_interest": 167000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.52, "volume": 243000, "open_interest": 172000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.55, "volume": 256000, "open_interest": 178000},
        ],
    },
    {
        "external_id": "equities-nvda-earnings-beat",
        "source": "seed",
        "title": "Will Nvidia beat next-quarter revenue expectations?",
        "slug": "nvidia-next-quarter-revenue-beat",
        "category": "equities",
        "status": "open",
        "close_time": "2026-05-28T21:00:00Z",
        "last_price": 0.71,
        "probability_change": 0.02,
        "volume": 333000,
        "open_interest": 276000,
        "description": "Single-name earnings market on whether Nvidia beats consensus revenue in its next quarterly report.",
        "metadata_json": {"desk": "equities", "tags": ["nvda", "earnings", "ai"]},
        "brief": {
            "summary": "The market remains strongly skewed toward a beat given demand durability in AI infrastructure, but expectations are already elevated.",
            "why_this_matters_now": "This contract captures the center of the current AI-exposed equity narrative and can spill into indexes and semiconductor peers.",
            "what_changed": "Odds firmed after supply-chain checks and hyperscaler commentary reinforced continued capex appetite.",
            "bull_case": "AI demand remains supply constrained and the company clears consensus with upside guidance.",
            "base_case": "Revenue beats modestly, but the market focuses more on guidance and gross margin durability than the beat itself.",
            "bear_case": "Expectations outrun reality, timing issues slip revenue, or margin commentary disappoints despite solid demand.",
            "catalysts": "Supplier commentary, hyperscaler capex plans, earnings call, consensus revisions.",
            "drivers": "Data-center demand, pricing mix, margin trajectory, customer concentration.",
            "risks": "The market may resolve correctly on a beat while the stock still sells off on valuation or forward-guide concerns.",
            "what_would_change_probability": "Positive channel checks raise odds. Any sign of order digestion or margin pressure reduces them.",
            "sources_json": [
                {"label": "Consensus earnings estimates", "type": "earnings"},
                {"label": "Hyperscaler capex commentary", "type": "industry"},
            ],
            "recent_headlines": [
                {
                    "title": "Hyperscaler capex commentary stays firm ahead of earnings season",
                    "source": "Semis Desk",
                    "published_at": "2026-04-17T13:50:00Z",
                    "why_it_matters": "The market still expects a beat because the demand backdrop remains unusually strong.",
                }
            ],
        },
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.67, "volume": 308000, "open_interest": 261000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.69, "volume": 321000, "open_interest": 269000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.71, "volume": 333000, "open_interest": 276000},
        ],
    },
    {
        "external_id": "equities-tsla-deliveries",
        "source": "seed",
        "title": "Will Tesla next-quarter deliveries exceed consensus?",
        "slug": "tesla-next-quarter-deliveries-above-consensus",
        "category": "equities",
        "status": "open",
        "close_time": "2026-07-02T20:00:00Z",
        "last_price": 0.42,
        "probability_change": -0.04,
        "volume": 228000,
        "open_interest": 166000,
        "description": "Single-name market on whether Tesla deliveries clear the current next-quarter consensus estimate.",
        "metadata_json": {"desk": "equities", "tags": ["tesla", "deliveries", "autos"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.49, "volume": 201000, "open_interest": 154000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.45, "volume": 215000, "open_interest": 160000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.42, "volume": 228000, "open_interest": 166000},
        ],
    },
    {
        "external_id": "equities-amzn-margin",
        "source": "seed",
        "title": "Will Amazon operating margin expand year-over-year next quarter?",
        "slug": "amazon-operating-margin-expand-next-quarter",
        "category": "equities",
        "status": "open",
        "close_time": "2026-08-02T21:00:00Z",
        "last_price": 0.64,
        "probability_change": 0.01,
        "volume": 146000,
        "open_interest": 102000,
        "description": "Single-name market focused on Amazon margin expansion versus the comparable quarter a year earlier.",
        "metadata_json": {"desk": "equities", "tags": ["amazon", "margin", "cloud"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.61, "volume": 138000, "open_interest": 97000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.63, "volume": 143000, "open_interest": 100000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.64, "volume": 146000, "open_interest": 102000},
        ],
    },
    {
        "external_id": "sports-nba-title-celtics",
        "source": "seed",
        "title": "Will the Celtics win the 2026 NBA title?",
        "slug": "celtics-win-2026-nba-title",
        "category": "sports",
        "status": "open",
        "close_time": "2026-06-30T05:00:00Z",
        "last_price": 0.23,
        "probability_change": 0.02,
        "volume": 119000,
        "open_interest": 87000,
        "description": "Championship market on whether Boston captures the 2026 NBA title.",
        "metadata_json": {"desk": "sports", "tags": ["nba", "title"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.20, "volume": 108000, "open_interest": 81000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.22, "volume": 114000, "open_interest": 84000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.23, "volume": 119000, "open_interest": 87000},
        ],
    },
    {
        "external_id": "sports-nfl-chiefs-playoffs",
        "source": "seed",
        "title": "Will the Chiefs make the 2026 NFL playoffs?",
        "slug": "chiefs-make-2026-nfl-playoffs",
        "category": "sports",
        "status": "open",
        "close_time": "2026-12-30T23:00:00Z",
        "last_price": 0.79,
        "probability_change": 0.01,
        "volume": 96000,
        "open_interest": 73000,
        "description": "Seasonal sports market on whether Kansas City reaches the NFL postseason.",
        "metadata_json": {"desk": "sports", "tags": ["nfl", "playoffs"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.77, "volume": 91000, "open_interest": 70000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.78, "volume": 94000, "open_interest": 71500},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.79, "volume": 96000, "open_interest": 73000},
        ],
    },
    {
        "external_id": "macro-ust10y-below-4",
        "source": "seed",
        "title": "Will the U.S. 10-year Treasury yield fall below 4.0% by July 2026?",
        "slug": "us10y-yield-below-4-by-july-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-07-31T21:00:00Z",
        "last_price": 0.66,
        "probability_change": 0.04,
        "volume": 188000,
        "open_interest": 129000,
        "description": "Rates market on whether the 10-year Treasury yield prints below 4.0% before August 2026.",
        "metadata_json": {"desk": "rates", "tags": ["treasury", "yields", "macro"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.60, "volume": 166000, "open_interest": 119000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.63, "volume": 177000, "open_interest": 124000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.66, "volume": 188000, "open_interest": 129000},
        ],
    },
    {
        "external_id": "politics-shutdown-2026",
        "source": "seed",
        "title": "Will the U.S. government shut down before October 2026?",
        "slug": "government-shutdown-before-october-2026",
        "category": "politics",
        "status": "open",
        "close_time": "2026-09-30T23:59:00Z",
        "last_price": 0.29,
        "probability_change": 0.05,
        "volume": 174000,
        "open_interest": 111000,
        "description": "Fiscal-politics market on whether a federal government shutdown occurs before the end of September 2026.",
        "metadata_json": {"desk": "dc", "tags": ["shutdown", "budget", "politics"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.22, "volume": 149000, "open_interest": 103000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.25, "volume": 161000, "open_interest": 107000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.29, "volume": 174000, "open_interest": 111000},
        ],
    },
    {
        "external_id": "crypto-stablecoin-bill",
        "source": "seed",
        "title": "Will Congress pass major stablecoin legislation by December 2026?",
        "slug": "major-stablecoin-legislation-by-december-2026",
        "category": "crypto",
        "status": "open",
        "close_time": "2026-12-31T23:00:00Z",
        "last_price": 0.48,
        "probability_change": 0.07,
        "volume": 132000,
        "open_interest": 91000,
        "description": "Policy market on whether the U.S. passes a major stablecoin bill by the end of 2026.",
        "metadata_json": {"desk": "policy", "tags": ["stablecoin", "crypto", "legislation"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.39, "volume": 109000, "open_interest": 82000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.43, "volume": 121000, "open_interest": 86000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.48, "volume": 132000, "open_interest": 91000},
        ],
    },
    {
        "external_id": "equities-msft-cloud-growth",
        "source": "seed",
        "title": "Will Microsoft cloud revenue growth exceed 30% year-over-year next quarter?",
        "slug": "microsoft-cloud-growth-above-30-next-quarter",
        "category": "equities",
        "status": "open",
        "close_time": "2026-07-30T21:00:00Z",
        "last_price": 0.54,
        "probability_change": 0.02,
        "volume": 198000,
        "open_interest": 134000,
        "description": "Single-name contract on Azure and broader cloud revenue momentum versus the year-ago quarter.",
        "metadata_json": {"desk": "equities", "tags": ["msft", "cloud", "earnings"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.51, "volume": 181000, "open_interest": 126000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.53, "volume": 190000, "open_interest": 130000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.54, "volume": 198000, "open_interest": 134000},
        ],
    },
    {
        "external_id": "equities-googl-search-rev",
        "source": "seed",
        "title": "Will Alphabet beat next-quarter search revenue expectations?",
        "slug": "alphabet-search-revenue-beat-next-quarter",
        "category": "equities",
        "status": "open",
        "close_time": "2026-08-15T21:00:00Z",
        "last_price": 0.62,
        "probability_change": 0.01,
        "volume": 156000,
        "open_interest": 104000,
        "description": "Earnings-adjacent market focused on Google Search and related advertising revenue vs consensus.",
        "metadata_json": {"desk": "equities", "tags": ["googl", "search", "ads"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.60, "volume": 148000, "open_interest": 99000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.61, "volume": 152000, "open_interest": 101000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.62, "volume": 156000, "open_interest": 104000},
        ],
    },
    {
        "external_id": "equities-meta-rd-loss",
        "source": "seed",
        "title": "Will Meta narrow Reality Labs operating losses by Q3 2026?",
        "slug": "meta-reality-labs-loss-narrow-q3-2026",
        "category": "equities",
        "status": "open",
        "close_time": "2026-10-01T21:00:00Z",
        "last_price": 0.41,
        "probability_change": -0.02,
        "volume": 124000,
        "open_interest": 88000,
        "description": "Tracks whether Meta’s Reality Labs segment shows a smaller loss versus the prior comparable quarter.",
        "metadata_json": {"desk": "equities", "tags": ["meta", "vr", "margin"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.44, "volume": 118000, "open_interest": 84000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.42, "volume": 121000, "open_interest": 86000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.41, "volume": 124000, "open_interest": 88000},
        ],
    },
    {
        "external_id": "macro-wti-85",
        "source": "seed",
        "title": "Will WTI crude oil trade above $85/bbl before October 2026?",
        "slug": "crude-wti-above-85-by-september-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-09-30T23:00:00Z",
        "last_price": 0.47,
        "probability_change": 0.03,
        "volume": 205000,
        "open_interest": 142000,
        "description": "Commodity-linked macro contract on WTI pricing through late 2026.",
        "metadata_json": {"desk": "commodities", "tags": ["oil", "inflation", "macro"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.43, "volume": 192000, "open_interest": 135000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.45, "volume": 199000, "open_interest": 139000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.47, "volume": 205000, "open_interest": 142000},
        ],
    },
    {
        "external_id": "macro-gold-3200",
        "source": "seed",
        "title": "Will gold futures settle above $3,200/oz by December 2026?",
        "slug": "gold-futures-above-3200-by-december-2026",
        "category": "macro",
        "status": "open",
        "close_time": "2026-12-30T23:00:00Z",
        "last_price": 0.52,
        "probability_change": 0.04,
        "volume": 178000,
        "open_interest": 121000,
        "description": "Precious-metals macro market tied to COMEX gold futures through year-end 2026.",
        "metadata_json": {"desk": "commodities", "tags": ["gold", "rates", "macro"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.47, "volume": 165000, "open_interest": 114000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.50, "volume": 172000, "open_interest": 118000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.52, "volume": 178000, "open_interest": 121000},
        ],
    },
    {
        "external_id": "tech-ai-chip-controls",
        "source": "seed",
        "title": "Will the U.S. expand advanced AI chip export controls before 2027?",
        "slug": "us-expands-ai-chip-export-controls-before-2027",
        "category": "politics",
        "status": "open",
        "close_time": "2026-12-31T23:00:00Z",
        "last_price": 0.58,
        "probability_change": 0.02,
        "volume": 143000,
        "open_interest": 97000,
        "description": "Geotech policy market on tighter semiconductor trade rules affecting AI accelerators.",
        "metadata_json": {"desk": "policy", "tags": ["semis", "export-controls", "ai"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.55, "volume": 136000, "open_interest": 92000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.57, "volume": 140000, "open_interest": 95000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.58, "volume": 143000, "open_interest": 97000},
        ],
    },
    {
        "external_id": "macro-eu-recession-2026",
        "source": "seed",
        "title": "Will the euro area enter recession before Q1 2027?",
        "slug": "euro-area-recession-before-q1-2027",
        "category": "macro",
        "status": "open",
        "close_time": "2027-03-31T22:00:00Z",
        "last_price": 0.35,
        "probability_change": -0.01,
        "volume": 112000,
        "open_interest": 78000,
        "description": "Regional growth contract tracking recession risk in the euro area over the next year.",
        "metadata_json": {"desk": "global", "tags": ["recession", "europe", "macro"]},
        "brief": None,
        "snapshots": [
            {"captured_at": "2026-04-12T20:00:00Z", "price": 0.37, "volume": 106000, "open_interest": 74000},
            {"captured_at": "2026-04-15T20:00:00Z", "price": 0.36, "volume": 109000, "open_interest": 76000},
            {"captured_at": "2026-04-17T20:00:00Z", "price": 0.35, "volume": 112000, "open_interest": 78000},
        ],
    },
]


def seed_demo_user(db: Session) -> None:
    """Seed a single demo user for local testing if enabled."""
    if not settings.seed_demo_user:
        return

    existing_user = db.scalar(select(User).where(User.email == settings.demo_user_email))
    if existing_user is not None:
        return

    user = User(
        email=settings.demo_user_email,
        password_hash=hash_password(settings.demo_user_password),
        display_name=settings.demo_user_display_name,
    )
    db.add(user)
    db.flush()

    db.add(
        UserProfile(
            user_id=user.id,
            bio="Seeded local demo account for PreTerm.",
            timezone="America/Chicago",
            theme="system",
        )
    )
    db.add(
        UserPreference(
            user_id=user.id,
            preferred_categories="[]",
            preferred_desk_mode="focused",
            alert_move_threshold=None,
            alert_headline_matches=True,
        )
    )
    db.add_all(
        [
            AlertPreference(user_id=user.id, rule_type="move_threshold", threshold_value=5, enabled=True),
            AlertPreference(user_id=user.id, rule_type="mapped_headline", threshold_value=None, enabled=True),
            AlertPreference(user_id=user.id, rule_type="threshold_range", threshold_value=60, enabled=True),
        ]
    )
    db.commit()


def seed_markets(db: Session) -> None:
    existing_market = db.scalar(select(Market.id).limit(1))
    if existing_market is not None:
        return

    for record in SEED_MARKETS:
        market = Market(
            external_id=record["external_id"],
            source=record["source"],
            title=record["title"],
            slug=record["slug"],
            category=record["category"],
            status=record["status"],
            close_time=_dt(record["close_time"]),
            last_price=record["last_price"],
            probability_change=record["probability_change"],
            volume=record["volume"],
            open_interest=record["open_interest"],
            description=record["description"],
            metadata_json=json.dumps(record["metadata_json"]) if record.get("metadata_json") else None,
        )
        db.add(market)
        db.flush()

        brief = record.get("brief")
        if isinstance(brief, dict):
            db.add(
                MarketBrief(
                    market_id=market.id,
                    summary=brief["summary"],
                    why_this_matters_now=brief["why_this_matters_now"],
                    what_changed=brief["what_changed"],
                    bull_case=brief["bull_case"],
                    base_case=brief["base_case"],
                    bear_case=brief["bear_case"],
                    catalysts=brief["catalysts"],
                    drivers=brief["drivers"],
                    risks=brief["risks"],
                    what_would_change_probability=brief["what_would_change_probability"],
                    sources_json=json.dumps(brief.get("sources_json", [])),
                    recent_headlines_json=json.dumps(brief.get("recent_headlines", [])),
                )
            )

        snapshots = record.get("snapshots", [])
        if isinstance(snapshots, list):
            for snapshot in snapshots:
                db.add(
                    MarketSnapshot(
                        market_id=market.id,
                        captured_at=_dt(snapshot["captured_at"]) or datetime.now(UTC),
                        price=snapshot["price"],
                        volume=snapshot.get("volume"),
                        open_interest=snapshot.get("open_interest"),
                        metadata_json=json.dumps(snapshot.get("metadata_json"))
                        if snapshot.get("metadata_json")
                        else None,
                    )
                )

        for entry in _generate_timeline_entries(record):
            db.add(
                MarketTimelineEntry(
                    market_id=market.id,
                    occurred_at=_dt(entry["occurred_at"]) or datetime.now(UTC),
                    move=entry.get("move"),
                    price_after_move=entry.get("price_after_move"),
                    reason=entry["reason"],
                    linked_label=entry.get("linked_label"),
                    linked_type=entry.get("linked_type"),
                    linked_url=entry.get("linked_url"),
                    metadata_json=json.dumps(entry.get("metadata_json"))
                    if entry.get("metadata_json")
                    else None,
                )
            )

    db.commit()
