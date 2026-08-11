import datetime
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import history
import render
from riot import RiotClient

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = ROOT / "graphs"
RECHECK_DAYS = 3
ROLE_SAMPLE = 20


def api_key():
    key = os.environ.get("RIOT_API_KEY", "")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "RIOT_API_KEY":
                key = value.strip().strip("'\"")
    if not key:
        raise SystemExit("RIOT_API_KEY is not set (environment variable or .env file)")
    return key


def slugify(game_name, tag_line):
    slug = f"{game_name}-{tag_line}".lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9-]", "", slug)


def day_bounds(day, tz):
    start = datetime.datetime.combine(day, datetime.time(), tzinfo=tz)
    end = start + datetime.timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp())


def update_player(client, entry, tz, today, window_start, queue):
    counts = entry.setdefault("counts", {})
    tracked = entry.get("trackedSince")
    tracked = datetime.date.fromisoformat(tracked) if tracked else None

    ranges = []
    if tracked is None:
        ranges.append((window_start, today))
    else:
        if window_start < tracked:
            ranges.append((window_start, tracked - datetime.timedelta(days=1)))
        fetched = datetime.date.fromisoformat(
            entry.get("fetchedThrough", today.isoformat())
        )
        ranges.append(
            (max(window_start, fetched - datetime.timedelta(days=RECHECK_DAYS - 1)), today)
        )

    total_days = sum((last - first).days + 1 for first, last in ranges if first <= last)
    print(f"  counting games over {total_days} day(s)...")
    for first, last in ranges:
        day = first
        while day <= last:
            start, end = day_bounds(day, tz)
            n = client.count_matches(entry["puuid"], start, end, queue)
            iso = day.isoformat()
            if n:
                counts[iso] = n
            else:
                counts.pop(iso, None)
            day += datetime.timedelta(days=1)

    entry["trackedSince"] = min(tracked or window_start, window_start).isoformat()
    entry["fetchedThrough"] = today.isoformat()


def update_top_role(client, entry):
    ids = client.recent_match_ids(entry["puuid"], ROLE_SAMPLE)
    cached = entry.get("roles", {})
    roles = {}
    for mid in ids:
        roles[mid] = cached[mid] if mid in cached else client.match_role(mid, entry["puuid"])
    entry["roles"] = roles
    tally = {}
    for role in roles.values():
        if role:
            tally[role] = tally.get(role, 0) + 1
    entry["topRole"] = max(tally, key=tally.get) if tally else None


def demo():
    import random

    rng = random.Random(7)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364)
    counts = {}
    day = start
    while day <= today:
        chance = 0.75 if day.weekday() >= 5 else 0.4
        if rng.random() < chance:
            counts[day.isoformat()] = rng.choice((1, 1, 2, 2, 3, 3, 4, 5, 7, 9))
        day += datetime.timedelta(days=1)

    GRAPHS.mkdir(exist_ok=True)
    tracked_since = start + datetime.timedelta(days=28)
    rank = {"queue": "solo", "tier": "EMERALD", "division": "II",
            "lp": 47, "wins": 210, "losses": 173}
    profile = {"iconId": 29, "level": 187}
    for theme in ("light", "dark"):
        svg = render.render(
            "Demo#EUW", counts, today=today, tracked_since=tracked_since,
            theme=theme, rank=rank, profile=profile, role="JUNGLE",
        )
        (GRAPHS / f"demo-{theme}.svg").write_text(svg)
        print(f"graphs/demo-{theme}.svg")


def main():
    if "--demo" in sys.argv:
        demo()
        return

    config = json.loads((ROOT / "config.json").read_text())
    key = api_key()
    tz = ZoneInfo(config.get("timezone", "UTC"))
    days = int(config.get("days", 365))
    queue = config.get("queue")
    today = datetime.datetime.now(tz).date()
    window_start = today - datetime.timedelta(days=days - 1)

    hist = history.load()
    GRAPHS.mkdir(exist_ok=True)

    for player in config["players"]:
        label = f"{player['gameName']}#{player['tagLine']}"
        print(f"[{label}]")
        client = RiotClient(key, player["region"])
        entry = hist["players"].setdefault(label, {})
        if "puuid" not in entry:
            entry["puuid"] = client.puuid(player["gameName"], player["tagLine"])

        update_player(client, entry, tz, today, window_start, queue)
        try:
            entry["rank"] = client.ranked_entry(entry["puuid"])
        except Exception as err:
            print(f"  rank lookup failed, keeping previous: {err}", file=sys.stderr)
        try:
            entry["profile"] = client.summoner_info(entry["puuid"])
        except Exception as err:
            print(f"  profile lookup failed, keeping previous: {err}", file=sys.stderr)
        try:
            update_top_role(client, entry)
        except Exception as err:
            print(f"  role lookup failed, keeping previous: {err}", file=sys.stderr)
        history.save(hist)

        slug = slugify(player["gameName"], player["tagLine"])
        tracked_since = datetime.date.fromisoformat(entry["trackedSince"])
        total = 0
        for theme in ("light", "dark"):
            svg = render.render(
                label, entry["counts"], today=today, days=days,
                tracked_since=tracked_since, theme=theme,
                rank=entry.get("rank"), profile=entry.get("profile"),
                role=entry.get("topRole"),
            )
            (GRAPHS / f"{slug}-{theme}.svg").write_text(svg)
        total = sum(
            n for iso, n in entry["counts"].items()
            if datetime.date.fromisoformat(iso) >= window_start
        )
        print(f"  {total} games in the last {days} days -> graphs/{slug}-light.svg + dark")


if __name__ == "__main__":
    main()
