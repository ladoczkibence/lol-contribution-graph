import base64
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMBLEMS = ROOT / "assets" / "emblems"
ICONS = ROOT / "assets" / "profileicons"

EMBLEM_URL = ("https://raw.communitydragon.org/latest/plugins/"
              "rcp-fe-lol-shared-components/global/default/{tier}.png")
VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
ICON_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{icon_id}.png"


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "lol-contribution-graph"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _cached(path, fetch):
    if path.exists():
        return path
    try:
        data = fetch()
    except Exception as err:
        print(f"  could not fetch {path.name}: {err}", file=sys.stderr)
        return None
    if not data.startswith(b"\x89PNG"):
        print(f"  unexpected content for {path.name}, skipping", file=sys.stderr)
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def emblem(tier):
    tier = tier.lower()
    return _cached(EMBLEMS / f"{tier}.png", lambda: _fetch(EMBLEM_URL.format(tier=tier)))


def profile_icon(icon_id):
    def fetch():
        version = json.loads(_fetch(VERSIONS_URL))[0]
        return _fetch(ICON_URL.format(version=version, icon_id=icon_id))

    return _cached(ICONS / f"{icon_id}.png", fetch)


def data_uri(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
