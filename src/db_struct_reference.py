import json
import time

INDICATOR_TYPES = ['PCTCHG', 'ABOVE', 'BELOW']

alert_structure = {'indicator': 'BELOW',
                   'target': 4100,
                   'alerted': False}
alert2 = {'indicator': 'ABOVE',
           'target': 4050,
           'alerted': False}

alerts_db = {'ETH/USDT': [alert_structure, alert2],
             'BTC/USDT': [alert_structure, alert2]}

print(alerts_db)
time.sleep(1)
print()

for pair in alerts_db.keys():
    removables = []
    for i, alert in enumerate(alerts_db[pair]):
        if alert['alerted']:
            removables.append(alert)
    for removable in removables:
        alerts_db[pair].remove(removable)
        print(f"Removed: {removable}")

print(alerts_db)

with open('src/alerts_db.json', 'w') as outfile:
    outfile.write(json.dumps(alerts_db, indent=2))