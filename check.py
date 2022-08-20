#! /usr/bin/env python3

import requests
import json
import time
import os

nb = 200 # increase if error given

with open('events.ndjson', 'r') as f:
    events = [json.loads(line) for line in f.read().splitlines()[:-1]]

now = time.time() * 1000
completed = list(filter(lambda x: x['finishesAt'] <= now , events))
completed_ids = [event['id'] for event in sorted(completed, key=lambda d: d['startsAt'])]

qualified_players = set()

def getEventResults(event):
    if not os.path.exists(f'{event}.ndjson') or os.system(f'wc -l {event}.ndjson') < nb:
        headers = {'Accept': 'application/x-ndjson', 'Content-Type': 'application/x-ndjson'}
        if os.path.exists('token'):
            with open('token', 'r') as f:
                tokendata = f.read()
            headers['Authorization'] = f'Bearer {tokendata}'
        results = requests.get(f'https://lichess.org/api/tournament/{event}/results?nb={nb}', headers=headers).text
        with open(f'{event}.ndjson', 'w') as f:
            f.write(results)
    with open(f'{event}.ndjson', 'r') as f:
        results = [json.loads(line) for line in f.read().splitlines()[:-1]]
    return results

for event in completed_ids:
    results = getEventResults(event)
    added = 0
    for n, player in enumerate(results):
        if player.get('title'):
            continue
        if player['username'] in qualified_players:
            continue
        qualified_players.add(player['username'])
        added += 1
        if added == 50:
            break
        if n == 199:
            print('Increase nb players pulled in parameter at the top of the file')
print(len(qualified_players))
print(qualified_players)
