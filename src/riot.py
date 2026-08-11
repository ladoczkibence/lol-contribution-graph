import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROUTING = {
    "br1": "americas", "la1": "americas", "la2": "americas", "na1": "americas",
    "oc1": "sea", "ph2": "sea", "sg2": "sea", "th2": "sea", "tw2": "sea", "vn2": "sea",
    "jp1": "asia", "kr": "asia",
    "eun1": "europe", "euw1": "europe", "me1": "europe", "ru": "europe", "tr1": "europe",
}

MIN_DELAY = 1.3


class RiotClient:
    def __init__(self, api_key, region):
        routing = ROUTING.get(region)
        if routing is None:
            raise SystemExit(
                f"unknown region '{region}' (expected one of: {', '.join(sorted(ROUTING))})"
            )
        self.base = f"https://{routing}.api.riotgames.com"
        self.platform_base = f"https://{region}.api.riotgames.com"
        self.api_key = api_key
        self._last_request = 0.0

    def _get(self, path, params=None, base=None):
        url = (base or self.base) + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(5):
            wait = MIN_DELAY - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, headers={
                "X-Riot-Token": self.api_key,
                "User-Agent": "lol-contribution-graph",
            })
            self._last_request = time.monotonic()
            try:
                with urllib.request.urlopen(req) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    retry_after = int(err.headers.get("Retry-After", "10"))
                    print(f"  rate limited, waiting {retry_after}s", file=sys.stderr)
                    time.sleep(retry_after)
                    continue
                if err.code in (500, 502, 503, 504):
                    time.sleep(5 * (attempt + 1))
                    continue
                if err.code in (401, 403):
                    raise SystemExit(
                        "Riot API rejected the key (401/403). Development keys expire "
                        "after 24h; get a personal key at https://developer.riotgames.com"
                    )
                raise
        raise SystemExit(f"giving up on {path} after repeated errors")

    def puuid(self, game_name, tag_line):
        path = (
            "/riot/account/v1/accounts/by-riot-id/"
            f"{urllib.parse.quote(game_name)}/{urllib.parse.quote(tag_line)}"
        )
        try:
            return self._get(path)["puuid"]
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise SystemExit(f"Riot ID {game_name}#{tag_line} not found") from None
            raise

    def ranked_entry(self, puuid):
        entries = self._get(
            f"/lol/league/v4/entries/by-puuid/{puuid}", base=self.platform_base
        )
        by_queue = {e.get("queueType"): e for e in entries}
        entry = by_queue.get("RANKED_SOLO_5x5") or by_queue.get("RANKED_FLEX_SR")
        if not entry:
            return None
        return {
            "queue": "solo" if entry["queueType"] == "RANKED_SOLO_5x5" else "flex",
            "tier": entry["tier"],
            "division": entry["rank"],
            "lp": entry["leaguePoints"],
            "wins": entry["wins"],
            "losses": entry["losses"],
        }

    def summoner_info(self, puuid):
        s = self._get(f"/lol/summoner/v4/summoners/by-puuid/{puuid}", base=self.platform_base)
        return {"iconId": s.get("profileIconId"), "level": s.get("summonerLevel")}

    def recent_match_ids(self, puuid, count=20):
        return self._get(
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids", {"start": 0, "count": count}
        )

    def match_role(self, match_id, puuid):
        match = self._get(f"/lol/match/v5/matches/{match_id}")
        for p in match.get("info", {}).get("participants", []):
            if p.get("puuid") == puuid:
                return p.get("teamPosition") or None
        return None

    def count_matches(self, puuid, start, end, queue=None):
        params = {"startTime": start, "endTime": end, "count": 100}
        if queue is not None:
            params["queue"] = queue
        ids = self._get(f"/lol/match/v5/matches/by-puuid/{puuid}/ids", params)
        if len(ids) == 100:
            print("  warning: 100+ games in one day, count is capped", file=sys.stderr)
        return len(ids)
