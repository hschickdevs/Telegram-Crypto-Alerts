import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'alerts_db.json')
if not os.path.isfile(DB_PATH):
    with open(DB_PATH, 'w+') as database:
        database.write(json.dumps({}, indent=2))


def load_db() -> dict:
    with open(DB_PATH, 'r') as infile:
        return json.load(infile)


def update_db(data: dict) -> None:
    with open(DB_PATH, 'w') as outfile:
        outfile.write(json.dumps(data, indent=2))
