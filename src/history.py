import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "history.json"


def load():
    if PATH.exists():
        return json.loads(PATH.read_text())
    return {"players": {}}


def save(history):
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n")
