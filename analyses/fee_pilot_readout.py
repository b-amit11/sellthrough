"""Fee pilot readout: did the 20% buyer fee pay for itself?

Reads the dbt marts in warehouse.duckdb and writes:
  reports/findings.json      every number quoted in reports/memo.md
  reports/figures/*.png      charts used in the memo
  exports/*.csv              mart extracts for the Looker Studio dashboard

Method: difference-in-differences on events, pilot markets vs control markets,
June 1 - July 25 events (pre) vs Aug 8 - Sep 30 events (post). The gaps around
Aug 1 keep events whose sales straddle the fee change out of both windows.
Estimates come from weighted least squares with category and market fixed
effects; intervals come from a 1,000-draw bootstrap over events.

Run: python analyses/fee_pilot_readout.py  (after dbt build)
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGS = REPORTS / "figures"
EXPORTS = ROOT / "exports"
rng = np.random.default_rng(7)

con = duckdb.connect(str(ROOT / "warehouse.duckdb"), read_only=True)

events = con.sql("""
    select
        *,
        case when event_date between date '2025-06-01' and date '2025-07-25' then 'pre'
             when event_date between date '2025-08-08' and date '2025-09-30' then 'post'
        end                                                   as period,
        market_name = 'Phoenix' and category = 'baseball'     as is_phoenix_baseball
    from fct_event_performance
    where not is_cancelled
""").df()
did = events[events.period.notna() & (events.tickets_listed > 0)].copy()
did["treated"] = (did.is_fee_pilot_market & (did.period == "post")).astype(float)
did["post"] = (did.period == "post").astype(float)


def did_estimate(df: pd.DataFrame, outcome: str) -> float:
    """Weighted DiD coefficient with category, market and post fixed effects."""
    X = pd.concat([
        df[["treated", "post"]],
        pd.get_dummies(df.category, prefix="c", drop_first=True, dtype=float),
        pd.get_dummies(df.market_name, prefix="m", drop_first=True, dtype=float),
    ], axis=1)
    X.insert(0, "const", 1.0)
    w = np.sqrt(df.tickets_listed.to_numpy(float))
    beta, *_ = np.linalg.lstsq(X.to_numpy(float) * w[:, None], df[outcome].to_numpy(float) * w, rcond=None)
    return float(beta[1])


def did_with_ci(df: pd.DataFrame, outcome: str, draws: int = 1000) -> dict:
    point = did_estimate(df, outcome)
    boots = [did_estimate(df.iloc[rng.integers(0, len(df), len(df))], outcome) for _ in range(draws)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"estimate": round(point, 4), "ci_low": round(float(lo), 4), "ci_high": round(float(hi), 4)}


def pooled(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["is_fee_pilot_market", "period"])
    return pd.DataFrame({
        "events": g.size(),
        "sell_through": g.tickets_sold.sum() / g.tickets_listed.sum(),
        "session_to_checkout": g.checkout_starts.sum() / g.sessions.sum(),
        "checkout_to_order": g.orders.sum() / g.checkout_starts.sum(),
        "sessions_per_event": g.sessions.sum() / g.size(),
    }).round(4)


clean = did[~did.is_phoenix_baseball]
findings: dict = {"windows": {"pre": "events 2025-06-01 to 2025-07-25", "post": "events 2025-08-08 to 2025-09-30"}}

# 1. Naive vs adjusted effect on sell-through.
findings["sell_through_did"] = {
    "naive_all_events": did_with_ci(did, "sell_through_rate"),
    "excluding_phoenix_baseball": did_with_ci(clean, "sell_through_rate"),
}

# 2. Funnel: which step moved?
findings["funnel_pooled"] = {
    k: v.reset_index().to_dict("records")
    for k, v in {"all_events_excl_phoenix_baseball": pooled(clean)}.items()
}
findings["funnel_did"] = {
    "session_to_checkout": did_with_ci(clean, "session_to_checkout_rate"),
    "checkout_to_order": did_with_ci(clean, "checkout_to_order_rate"),
}

# 3. Phoenix baseball: demand, not fees.
phx = con.sql("""
    with g as (
        select event_date, sessions, sell_through_rate, home_team_last10_win_pct
        from fct_event_performance
        where market_name = 'Phoenix' and category = 'baseball'
          and event_date between date '2025-06-01' and date '2025-09-30'
    )
    select
        case when event_date < date '2025-08-01' then 'Jun-Jul' else 'Aug-Sep' end as window,
        count(*)                                   as home_games,
        round(avg(home_team_last10_win_pct), 3)    as avg_last10_win_pct,
        round(avg(sessions))                       as sessions_per_game,
        round(avg(sell_through_rate), 4)           as avg_sell_through
    from g group by 1 order by 1 desc
""").df()
findings["phoenix_baseball"] = phx.to_dict("records")

# 4. Economics by day type: did the higher fee pay for itself?
econ = {}
# Revenue per listed ticket = sell-through x avg price x take rate. Sellers set
# prices, so the pilot moves sell-through (measured) and the take rate (known:
# 15% + 10% -> 20% + 10% of ticket sales). Comparing dollars directly would mix
# in shifts in which events happened to be on sale in each window.
OLD_TAKE, NEW_TAKE = 0.25, 0.30
OLD_ALL_IN, NEW_ALL_IN = 1.15, 1.20
for day_type, df in clean.groupby("day_type"):
    st = did_with_ci(df, "sell_through_rate")
    pilot_post = df[(df.is_fee_pilot_market) & (df.period == "post")]
    actual = pilot_post.tickets_sold.sum() / pilot_post.tickets_listed.sum()

    def effects(delta: float) -> tuple[float, float]:
        volume = actual / (actual - delta)   # sold tickets vs. no-pilot counterfactual
        return volume * NEW_TAKE / OLD_TAKE - 1, volume * NEW_ALL_IN / OLD_ALL_IN - 1

    rev, gmv = effects(st["estimate"])
    # A larger sell-through loss (ci_low) gives the smaller revenue effect.
    rev_lo, gmv_lo = effects(st["ci_low"])
    rev_hi, gmv_hi = effects(st["ci_high"])
    econ[day_type] = {
        "events": int(len(df)),
        "sell_through_change_pts": st,
        "pilot_post_sell_through": round(float(actual), 4),
        "tickets_sold_change_pct": round(actual / (actual - st["estimate"]) - 1, 4),
        "net_revenue_change_pct": {"estimate": round(rev, 4), "ci_low": round(rev_lo, 4), "ci_high": round(rev_hi, 4)},
        "gmv_change_pct": {"estimate": round(gmv, 4), "ci_low": round(gmv_lo, 4), "ci_high": round(gmv_hi, 4)},
    }
findings["economics_by_day_type"] = econ

# 5. Weekly checkout conversion for the chart.
weekly = con.sql("""
    select date_trunc('week', activity_date) as week, is_fee_pilot_market,
           sum(orders) / sum(checkout_starts) as checkout_to_order
    from fct_market_daily
    where activity_date between date '2025-04-07' and date '2025-11-30'
    group by all order by 1
""").df()

(REPORTS).mkdir(exist_ok=True)
(REPORTS / "findings.json").write_text(json.dumps(findings, indent=2, default=str))

# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #

FIGS.mkdir(parents=True, exist_ok=True)
PILOT, CONTROL, MUTED = "#c2410c", "#2563eb", "#6b7280"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(8, 3.6))
for flag, color, label in [(True, PILOT, "Pilot markets (fee 15% → 20%)"), (False, CONTROL, "Control markets (fee 15%)")]:
    s = weekly[weekly.is_fee_pilot_market == flag]
    ax.plot(s.week, s.checkout_to_order * 100, color=color, lw=2, label=label)
ax.axvline(pd.Timestamp("2025-08-01"), color=MUTED, ls="--", lw=1)
ax.text(pd.Timestamp("2025-08-04"), 42.6, "Fee pilot\nstarts Aug 1", color=MUTED, va="center")
ax.set_ylabel("Checkout → order (%)")
ax.set_title("Checkout conversion fell only where the fee went up", loc="left", fontweight="bold")
ax.legend(frameon=False, loc="lower left")
fig.tight_layout()
fig.savefig(FIGS / "checkout_conversion_weekly.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.2))
labels = ["Naive estimate\n(all events)", "Excluding Phoenix\nbaseball slump"]
vals = [findings["sell_through_did"]["naive_all_events"], findings["sell_through_did"]["excluding_phoenix_baseball"]]
y = np.arange(len(vals))
ax.barh(y, [v["estimate"] * 100 for v in vals], color=[MUTED, PILOT], height=0.5)
ax.errorbar([v["estimate"] * 100 for v in vals], y,
            xerr=[[(v["estimate"] - v["ci_low"]) * 100 for v in vals], [(v["ci_high"] - v["estimate"]) * 100 for v in vals]],
            fmt="none", ecolor="black", capsize=4, lw=1)
for i, v in enumerate(vals):
    ax.text(v["ci_low"] * 100 - 0.2, i, f"{v['estimate']*100:.1f} pts", va="center", ha="right")
ax.set_yticks(y, labels)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlim(min(v["ci_low"] for v in vals) * 100 - 2.5, max(max(v["ci_high"] for v in vals) * 100 + 1, 0.5))
ax.set_xlabel("Change in sell-through caused by the pilot (percentage points, 95% CI)")
ax.set_title("A team slump inflates the naive fee effect", loc="left", fontweight="bold")
fig.tight_layout()
fig.savefig(FIGS / "sell_through_effect.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.2))
day_types = ["weeknight", "weekend"]
metrics = [("net_revenue_change_pct", PILOT, "Net revenue", -0.18), ("gmv_change_pct", CONTROL, "GMV", 0.18)]
x = np.arange(len(day_types))
all_vals = []
for key, color, label, off in metrics:
    v = [econ[d][key] for d in day_types]
    est = np.array([e["estimate"] for e in v]) * 100
    lo = est - np.array([e["ci_low"] for e in v]) * 100
    hi = np.array([e["ci_high"] for e in v]) * 100 - est
    ax.bar(x + off, est, 0.36, color=color, label=label)
    ax.errorbar(x + off, est, yerr=[lo, hi], fmt="none", ecolor="black", capsize=4, lw=1)
    for xi, e, h in zip(x + off, est, hi):
        ax.text(xi + 0.03, e + (h + 0.6 if e >= 0 else -0.6), f"{e:+.1f}%", ha="left",
                va="bottom" if e >= 0 else "top")
    all_vals += list(est - lo) + list(est + hi)
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x, ["Weeknight (Mon–Thu)", "Weekend (Fri–Sun)"])
ax.set_ylabel("Effect of pilot (%, 95% CI)")
ax.set_ylim(min(all_vals) - 5, max(all_vals) + 5)
ax.set_title("The higher fee pays on weekends, not on weeknights", loc="left", fontweight="bold")
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(FIGS / "economics_by_day_type.png", dpi=160)
plt.close(fig)

# --------------------------------------------------------------------------- #
# Looker Studio extracts
# --------------------------------------------------------------------------- #

EXPORTS.mkdir(exist_ok=True)
for table in ["fct_event_performance", "fct_market_daily", "fct_buyer_cohorts"]:
    con.sql(f"copy (select * from {table}) to '{EXPORTS / (table + '.csv')}' (header)")

print(json.dumps(findings, indent=2, default=str))
