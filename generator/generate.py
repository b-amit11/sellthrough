"""Generate a synthetic secondary-ticket marketplace for calendar year 2025.

The data is fictional. Two effects are planted so the analysis has something
real to find, and both are stored in tables an analyst could discover:

1. Buyer fee pilot: from 2025-08-01 the buyer service fee rises from 15% to 20%
   in three pilot markets (see fee_schedule). Buyers see the fee at checkout,
   so the effect shows up as lower checkout-to-order conversion, strongest for
   weeknight and low-price events.
2. Team slump: the Phoenix baseball team collapses in August (see team_games).
   Demand for its home games falls, which shows up as fewer sessions, not as
   lower conversion. Phoenix is also a pilot market, so a naive pilot-vs-control
   comparison overstates the fee effect.

Run: python generator/generate.py  (writes Parquet files to data/raw/)
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
YEAR_START = dt.date(2025, 1, 1)
YEAR_END = dt.date(2025, 12, 31)
PILOT_START = dt.date(2025, 8, 1)
BASE_BUYER_FEE = 0.15
PILOT_BUYER_FEE = 0.20
SELLER_FEE = 0.10

# --------------------------------------------------------------------------- #
# Markets, venues, teams
# --------------------------------------------------------------------------- #

MARKETS = [
    # market, state, pilot, baseball, arena league, arena team, football team
    ("Denver", "CO", False, "Denver Lumberjacks", "basketball", "Denver Altitude", "Denver Summit"),
    ("Phoenix", "AZ", True, "Phoenix Scorpions", "hockey", "Phoenix Dust Devils", None),
    ("Charlotte", "NC", False, "Charlotte Copperheads", "basketball", "Charlotte Hornbills", "Charlotte Ironclads"),
    ("Portland", "OR", False, "Portland Rivermen", "basketball", "Portland Timber Wolves", None),
    ("Nashville", "TN", True, "Nashville Fiddlers", "hockey", "Nashville Steel", "Nashville Outlaws"),
    ("Austin", "TX", False, "Austin Armadillos", "hockey", "Austin Longhorns HC", None),
    ("Columbus", "OH", True, "Columbus Clippers FC", "hockey", "Columbus Navigators", None),
    ("Sacramento", "CA", False, "Sacramento Gold Rush", "basketball", "Sacramento Monarchs", None),
]
SLUMP_TEAM = "Phoenix Scorpions"
SLUMP_START = dt.date(2025, 8, 1)

FACE = {"baseball": 38, "basketball": 95, "hockey": 78, "football": 145,
        "concert": 105, "theater": 88, "comedy": 52}
RESALE_SHARE = {"baseball": 0.018, "basketball": 0.035, "hockey": 0.03, "football": 0.022,
                "concert": 0.04, "theater": 0.05, "comedy": 0.06}
DOW_DEMAND = {0: 0.82, 1: 0.76, 2: 0.80, 3: 0.92, 4: 1.22, 5: 1.30, 6: 1.08}

markets = pd.DataFrame(
    [(i + 1, m[0], m[1], m[2]) for i, m in enumerate(MARKETS)],
    columns=["market_id", "market_name", "state", "is_fee_pilot_market"],
)

venue_rows, team_rows = [], []
vid = 0
for i, (mkt, _, _, bb, arena_league, arena_team, fb) in enumerate(MARKETS):
    mid = i + 1
    vid += 1
    venue_rows.append((vid, f"{mkt} Ballpark", mid, "ballpark", int(rng.integers(38000, 43000))))
    team_rows.append((bb, "baseball", mid, vid))
    vid += 1
    venue_rows.append((vid, f"{mkt} Arena", mid, "arena", int(rng.integers(17500, 20000))))
    team_rows.append((arena_team, arena_league, mid, vid))
    vid += 1
    venue_rows.append((vid, f"{mkt} Playhouse", mid, "theater", int(rng.integers(1800, 2900))))
    if fb:
        vid += 1
        venue_rows.append((vid, f"{mkt} Stadium", mid, "stadium", int(rng.integers(64000, 71000))))
        team_rows.append((fb, "football", mid, vid))

venues = pd.DataFrame(venue_rows, columns=["venue_id", "venue_name", "market_id", "venue_type", "capacity"])

# --------------------------------------------------------------------------- #
# Performers
# --------------------------------------------------------------------------- #

ADJ = ["Velvet", "Neon", "Paper", "Midnight", "Golden", "Silver", "Hollow", "Electric", "Wild",
       "Quiet", "Crimson", "Lunar", "Static", "Desert", "Glass", "Northern", "Lucky", "Broken"]
NOUN = ["Foxes", "Harbors", "Echoes", "Satellites", "Lanterns", "Rivers", "Hearts", "Saints",
        "Wolves", "Machines", "Parade", "Comets", "Tides", "Ghosts", "Pilots", "Gardens"]
FIRST = ["Maya", "Jordan", "Priya", "Luis", "Dana", "Theo", "Aisha", "Marcus", "Nina", "Sam",
         "Elena", "Kofi", "Rosa", "Ben", "Hana", "Omar", "Iris", "Diego", "June", "Ravi"]
LAST = ["Okafor", "Lindqvist", "Park", "Moreno", "Hale", "Brennan", "Sato", "Castillo",
        "Whitaker", "Nguyen", "Adler", "Mensah", "Reyes", "Kowalski", "Fontaine", "Ibarra"]
SHOWS = ["Northbound", "The Lighthouse Keeper", "Glass Menagerie Revue", "Paper Moons",
         "The Last Ferry", "Copper & Coal", "Starlight Express Line", "A Winter Almanac",
         "The Clockmaker", "Harbor Lights", "Dust Bowl Ballads", "The Understudy"]

perf_rows = []
pid = 0
team_pid = {}
for name, league, mid, venue_id in team_rows:
    pid += 1
    team_pid[name] = pid
    perf_rows.append((pid, name, "team", league, float(np.round(rng.lognormal(0, 0.18), 3))))

artist_names = set()
while len(artist_names) < 140:
    artist_names.add(f"The {rng.choice(ADJ)} {rng.choice(NOUN)}" if rng.random() < 0.6
                     else f"{rng.choice(FIRST)} {rng.choice(LAST)}")
for a in sorted(artist_names):
    pid += 1
    perf_rows.append((pid, a, "artist", "concert", float(np.round(rng.lognormal(0, 0.45), 3))))
for s in SHOWS:
    pid += 1
    perf_rows.append((pid, s, "show", "theater", float(np.round(rng.lognormal(0, 0.3), 3))))
comics = set()
while len(comics) < 45:
    comics.add(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
for c in sorted(comics):
    pid += 1
    perf_rows.append((pid, c, "comedian", "comedy", float(np.round(rng.lognormal(0, 0.4), 3))))

performers = pd.DataFrame(perf_rows, columns=["performer_id", "performer_name", "performer_type",
                                              "category", "popularity"])

# --------------------------------------------------------------------------- #
# Schedules
# --------------------------------------------------------------------------- #


def daterange(a: dt.date, b: dt.date):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


event_rows = []        # (performer_id, opponent, venue_id, date, hour, minute)
game_rows = []         # every game for form: (team, date, is_home)
booked = set()         # (venue_id, date)

for name, league, mid, venue_id in team_rows:
    p = team_pid[name]
    if league == "baseball":
        d = dt.date(2025, 3, 27)
        home = bool(rng.random() < 0.5)
        while d <= dt.date(2025, 9, 28):
            length = int(rng.choice([3, 3, 3, 4, 6, 7]))
            for k in range(length):
                day = d + dt.timedelta(days=k)
                if day > dt.date(2025, 9, 28):
                    break
                if rng.random() < 0.08:  # off day
                    continue
                game_rows.append((name, day, home))
                if home:
                    hr, mn = (13, 10) if day.weekday() in (5, 6) and rng.random() < 0.6 else (19, 5)
                    event_rows.append((p, venue_id, day, hr, mn))
                    booked.add((venue_id, day))
            d += dt.timedelta(days=length + int(rng.integers(0, 2)))
            home = not home
    elif league in ("basketball", "hockey"):
        windows = [(dt.date(2025, 1, 2), dt.date(2025, 4, 12)), (dt.date(2025, 10, 22), dt.date(2025, 12, 30))]
        for a, b in windows:
            d = a
            while d <= b:
                home = bool(rng.random() < 0.5)
                game_rows.append((name, d, home))
                if home:
                    event_rows.append((p, venue_id, d, 19, 30 if league == "basketball" else 0))
                    booked.add((venue_id, d))
                d += dt.timedelta(days=int(rng.choice([1, 2, 2, 3])))
    else:  # football, Sundays
        sundays = [d for d in daterange(dt.date(2025, 1, 5), dt.date(2025, 1, 5))] + \
                  [d for d in daterange(dt.date(2025, 9, 7), dt.date(2025, 12, 28)) if d.weekday() == 6]
        for k, d in enumerate(sundays):
            home = (k % 2 == 0)
            game_rows.append((name, d, home))
            if home:
                event_rows.append((p, venue_id, d, 13, 0))
                booked.add((venue_id, d))

artists = performers[performers.category == "concert"]
shows = performers[performers.category == "theater"]
comedians = performers[performers.category == "comedy"]

for _, v in venues.iterrows():
    if v.venue_type == "arena":
        n_target, pool, hour = 48, artists, 20
    elif v.venue_type == "theater":
        n_target, pool, hour = 95, None, 19
    elif v.venue_type == "stadium":
        n_target, pool, hour = 3, artists[artists.popularity > 1.6], 19
    else:
        n_target, pool, hour = 2, artists[artists.popularity > 1.6], 19
    days = [d for d in daterange(YEAR_START, YEAR_END) if (v.venue_id, d) not in booked]
    if v.venue_type in ("stadium", "ballpark"):
        days = [d for d in days if 6 <= d.month <= 8 and d.weekday() in (4, 5)]
    w = np.array([1.8 if d.weekday() in (4, 5) else 1.0 for d in days])
    chosen = rng.choice(len(days), size=min(n_target, len(days)), replace=False, p=w / w.sum())
    for idx in sorted(chosen):
        d = days[idx]
        if v.venue_type == "theater":
            perf = (shows if rng.random() < 0.6 else comedians).sample(1, random_state=int(rng.integers(1e9)))
        else:
            perf = pool.sample(1, random_state=int(rng.integers(1e9)))
        event_rows.append((int(perf.performer_id.iloc[0]), v.venue_id, d, hour, 0))
        booked.add((v.venue_id, d))

events = pd.DataFrame(event_rows, columns=["performer_id", "venue_id", "event_date", "hour", "minute"])
events = events.sort_values(["event_date", "venue_id"]).reset_index(drop=True)
events.insert(0, "event_id", np.arange(1, len(events) + 1))
events["event_start_local"] = pd.to_datetime(events.event_date) + \
    pd.to_timedelta(events.hour, unit="h") + pd.to_timedelta(events.minute, unit="m")
events = events.merge(performers[["performer_id", "category", "popularity", "performer_name"]], on="performer_id")
events = events.merge(venues[["venue_id", "market_id", "capacity"]], on="venue_id")
events = events.sort_values("event_id").reset_index(drop=True)

# Small number of cancelled events (orders get refunded).
events["is_cancelled"] = rng.random(len(events)) < 0.004

# --------------------------------------------------------------------------- #
# Team results and form
# --------------------------------------------------------------------------- #

games = pd.DataFrame(game_rows, columns=["team_name", "game_date", "is_home"]).sort_values(["team_name", "game_date"])
strength = {name: rng.uniform(0.44, 0.58) for name, *_ in team_rows}
strength[SLUMP_TEAM] = 0.56
win_p = games.apply(lambda r: 0.24 if (r.team_name == SLUMP_TEAM and r.game_date >= SLUMP_START)
                    else strength[r.team_name], axis=1)
games["won"] = rng.random(len(games)) < win_p.values
games["last10_win_pct"] = games.groupby("team_name")["won"].transform(
    lambda s: s.shift(1).rolling(10, min_periods=1).mean()).fillna(0.5).round(3)
games["team_id"] = games.team_name.map(team_pid)
team_games = games[["team_id", "team_name", "game_date", "is_home", "won", "last10_win_pct"]].reset_index(drop=True)

form = team_games[team_games.is_home].rename(columns={"team_id": "performer_id", "game_date": "event_date"})
events = events.merge(form[["performer_id", "event_date", "last10_win_pct"]], on=["performer_id", "event_date"], how="left")

# --------------------------------------------------------------------------- #
# Demand index per event
# --------------------------------------------------------------------------- #

dow = pd.to_datetime(events.event_date).dt.weekday
form_mult = np.where(events.last10_win_pct.notna(),
                     np.clip(1 + 1.1 * (events.last10_win_pct.fillna(0.5) - 0.5), 0.55, 1.4), 1.0)
summer = np.where((events.category == "baseball") & pd.to_datetime(events.event_date).dt.month.isin([6, 7, 8]), 1.08, 1.0)
holiday = np.where(pd.to_datetime(events.event_date).dt.month == 12, 1.06, 1.0)
events["demand_index"] = (events.popularity * dow.map(DOW_DEMAND).values * form_mult * summer * holiday
                          * rng.lognormal(0, 0.18, len(events))).round(4)
events["face_value"] = (events.category.map(FACE) * events.popularity ** 0.5).round(2)

# --------------------------------------------------------------------------- #
# Listings and orders
# --------------------------------------------------------------------------- #

pilot_markets = set(markets.loc[markets.is_fee_pilot_market, "market_id"])
QTY = np.array([1, 2, 2, 2, 2, 3, 4, 4, 4, 6, 8])
ZONES = np.array(["Lower", "Club", "Upper", "Upper", "Field", "Mezzanine"])

lst_parts = []
for ev in events.itertuples(index=False):
    exp_tickets = ev.capacity * RESALE_SHARE[ev.category] * (0.75 + 0.35 * ev.demand_index)
    n = max(3, rng.poisson(exp_tickets / 3.2))
    qty = rng.choice(QTY, n)
    listed_days_before = np.clip(1 + rng.exponential(24, n), 1, 120)
    listed_at = pd.Timestamp(ev.event_start_local) - pd.to_timedelta(listed_days_before, unit="D")
    # Sellers price partly on expected demand; zone moves price around.
    zone = rng.choice(ZONES, n)
    zone_mult = pd.Series(zone).map({"Field": 1.9, "Club": 1.6, "Lower": 1.3, "Mezzanine": 1.0, "Upper": 0.75}).values
    markup = np.exp(0.05 + 0.35 * np.log(ev.demand_index) + rng.normal(0, 0.32, n))
    price = np.round(ev.face_value * zone_mult * markup, 2)
    price = np.maximum(price, 8.0)

    # Candidate sale moment: concentrated close to the event.
    sale_days_before = listed_days_before * rng.beta(0.75, 2.2, n)
    sale_at = pd.Timestamp(ev.event_start_local) - pd.to_timedelta(sale_days_before, unit="D")

    # Purchase probability: demand up, relative price down.
    rel_price = markup * np.exp(rng.normal(0, 0.1, n))
    logit = 0.55 + 1.7 * np.log(ev.demand_index) - 2.4 * np.log(rel_price)
    in_pilot = (ev.market_id in pilot_markets) & (sale_at >= pd.Timestamp(PILOT_START))
    weeknight = pd.Timestamp(ev.event_date).weekday() in (0, 1, 2, 3)
    low_price = price < 60
    gamma = np.where(low_price, 7.5, 4.0) * (1.35 if weeknight else 0.7)
    fee_penalty = gamma * np.log((1 + PILOT_BUYER_FEE) / (1 + BASE_BUYER_FEE))
    p_base = 1 / (1 + np.exp(-logit))
    p_actual = 1 / (1 + np.exp(-(logit - np.where(in_pilot, fee_penalty, 0.0))))
    u = rng.random(n)
    would_sell = u < p_base
    sold = u < p_actual

    unsold_status = np.where(rng.random(n) < 0.12, "delisted", "expired")
    status = np.where(sold, "sold", unsold_status)
    lst_parts.append(pd.DataFrame({
        "event_id": ev.event_id,
        "seat_zone": zone,
        "quantity": qty,
        "list_price": price,
        "listed_at": listed_at.round("min"),
        "listing_status": status,
        "_sale_at": sale_at.round("min"),
        "_would_sell": would_sell,
        "_buyer_fee_pct": np.where(in_pilot, PILOT_BUYER_FEE, BASE_BUYER_FEE),
    }))

listings = pd.concat(lst_parts, ignore_index=True)
listings.insert(0, "listing_id", np.arange(100001, 100001 + len(listings)))
listings["seller_id"] = rng.integers(1, 38000, len(listings))
# Delisted listings come down partway between listing and event.
ev_start = listings.event_id.map(events.set_index("event_id").event_start_local)
dl = listings.listing_status == "delisted"
listings["delisted_at"] = pd.NaT
listings.loc[dl, "delisted_at"] = (listings.loc[dl, "listed_at"] +
                                   (ev_start[dl] - listings.loc[dl, "listed_at"]) * rng.uniform(0.2, 0.9, dl.sum())).dt.round("min")

# Buyers: a long-tailed pool so some buyers come back.
n_buyers = 160000
buyer_market = rng.integers(1, len(MARKETS) + 1, n_buyers)
buyers = pd.DataFrame({
    "buyer_id": np.arange(1, n_buyers + 1),
    "home_market_id": buyer_market,
    "signup_date": (pd.Timestamp("2021-01-01") + pd.to_timedelta(rng.integers(0, 1790, n_buyers), unit="D")).date,
})

sold = listings[listings.listing_status == "sold"].copy()
ev_mkt = sold.event_id.map(events.set_index("event_id").market_id).values
# Pick a buyer mostly from the event's market, with Zipf-like reuse.
buyer_by_mkt = {m: buyers.loc[buyers.home_market_id == m, "buyer_id"].values for m in range(1, len(MARKETS) + 1)}
pick = []
for m in ev_mkt:
    pool = buyer_by_mkt[m if rng.random() < 0.88 else int(rng.integers(1, len(MARKETS) + 1))]
    idx = min(int(rng.zipf(1.35)) - 1, len(pool) - 1) if rng.random() < 0.55 else int(rng.integers(len(pool)))
    pick.append(pool[idx])
cancelled = sold.event_id.map(events.set_index("event_id").is_cancelled).values
orders = pd.DataFrame({
    "order_id": np.arange(5000001, 5000001 + len(sold)),
    "listing_id": sold.listing_id.values,
    "event_id": sold.event_id.values,
    "buyer_id": pick,
    "quantity": sold.quantity.values,
    "ticket_price": sold.list_price.values,
    "buyer_fee_amount": np.round(sold.list_price.values * sold.quantity.values * sold._buyer_fee_pct.values, 2),
    "seller_fee_amount": np.round(sold.list_price.values * sold.quantity.values * SELLER_FEE, 2),
    "ordered_at": sold._sale_at.values,
    "platform": rng.choice(["ios", "android", "web"], len(sold), p=[0.46, 0.22, 0.32]),
    "order_status": np.where(cancelled, "refunded", "completed"),
})

# --------------------------------------------------------------------------- #
# Daily funnel per event (sessions -> checkout starts -> orders)
# --------------------------------------------------------------------------- #

listings["_would_day"] = listings._sale_at.dt.date
would = listings[listings._would_sell].groupby(["event_id", "_would_day"]).size().rename("would_orders")
actual = orders.assign(d=pd.to_datetime(orders.ordered_at).dt.date).groupby(["event_id", "d"]).size().rename("orders")
actual.index.names = ["event_id", "_would_day"]
funnel = pd.concat([would, actual], axis=1).fillna(0).reset_index().rename(columns={"_would_day": "activity_date"})
# Fill every day from 30 days before the event so browsing-only days exist.
grid = events[["event_id", "event_date"]].copy()
grid["activity_date"] = grid.event_date.apply(lambda d: [d - dt.timedelta(days=k) for k in range(30)])
grid = grid.explode("activity_date")[["event_id", "activity_date"]]
funnel = grid.merge(funnel, on=["event_id", "activity_date"], how="outer").fillna(0)
funnel = funnel.merge(events[["event_id", "demand_index"]], on="event_id")
CHECKOUT_CONV, SESSION_TO_CHECKOUT = 0.44, 0.085
base_browse = rng.poisson(6 * funnel.demand_index.values)
checkout = funnel.would_orders.values + rng.poisson(funnel.would_orders.values * (1 - CHECKOUT_CONV) / CHECKOUT_CONV)
checkout = np.maximum(checkout, funnel.orders.values).astype(int)
sessions = checkout + rng.poisson(checkout * (1 - SESSION_TO_CHECKOUT) / SESSION_TO_CHECKOUT) + base_browse
event_traffic_daily = pd.DataFrame({
    "event_id": funnel.event_id.astype(int),
    "activity_date": pd.to_datetime(funnel.activity_date).dt.date,
    "sessions": sessions.astype(int),
    "checkout_starts": checkout,
    "orders": funnel.orders.astype(int),
}).sort_values(["event_id", "activity_date"])
# Orders are recorded in the orders table; the traffic feed carries only the
# upstream funnel steps, as a web-analytics export would.
event_traffic_daily = event_traffic_daily.drop(columns="orders")

fee_schedule = pd.DataFrame(
    [(m, "2000-01-01", "2025-07-31" if m in pilot_markets else "2099-12-31", BASE_BUYER_FEE, SELLER_FEE)
     for m in markets.market_id] +
    [(m, "2025-08-01", "2099-12-31", PILOT_BUYER_FEE, SELLER_FEE) for m in sorted(pilot_markets)],
    columns=["market_id", "effective_from", "effective_to", "buyer_fee_pct", "seller_fee_pct"],
)

# --------------------------------------------------------------------------- #
# Write
# --------------------------------------------------------------------------- #

events_out = events[["event_id", "performer_id", "venue_id", "event_start_local", "face_value", "is_cancelled"]]
listings_out = listings[["listing_id", "event_id", "seller_id", "seat_zone", "quantity", "list_price",
                         "listed_at", "delisted_at", "listing_status"]]
performers_out = performers[["performer_id", "performer_name", "performer_type", "category"]]
tables = {
    "markets": markets, "venues": venues, "performers": performers_out, "events": events_out,
    "team_games": team_games, "listings": listings_out, "orders": orders, "buyers": buyers,
    "event_traffic_daily": event_traffic_daily, "fee_schedule": fee_schedule,
}
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()
for name, df in tables.items():
    con.register("df", df)
    con.execute(f"COPY df TO '{OUT / (name + '.parquet')}' (FORMAT parquet)")
    con.unregister("df")
    print(f"{name:22s} {len(df):>9,d} rows")
