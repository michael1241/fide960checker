#! /usr/bin/env python3

import requests
import json
import time
import os
import subprocess
import itertools
import platform

nb = 200 # increase if error given

with open('events.ndjson', 'r') as f:
    events = [json.loads(line) for line in f.read().splitlines()]

if os.path.exists('excludeplayers'):
    with open('excludeplayers', 'r') as f:
        exclude_players = set(f.read().splitlines())

now = time.time() * 1000
completed = list(filter(lambda x: x['finishesAt'] <= now , events))
completed_ids = [event['id'] for event in sorted(completed, key=lambda d: d['startsAt'])]

qualified_players = set()

def linecount(event):
    system = platform.system()
    if system ==  "Linux": return int(subprocess.check_output(['wc', '-l', f'{event}.ndjson']).split()[0])
    if system == "Windows": return sum(1 for _ in open(f'{event}.ndjson'))

def getEventResults(event):
    if not os.path.exists(f'{event}.ndjson') or linecount(event) < nb:
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
    time.sleep(2)
    added = 0
    for n, player in enumerate(results):
        if player.get('title') and player.get('title') != 'LM':
            continue
        if player['username'] in qualified_players:
            continue
        if player['username'] in exclude_players:
            continue
        qualified_players.add(player['username'])
        added += 1
        if added == 50:
            break
        if n == 199:
            print('Increase nb players pulled in parameter at the top of the file')

def chunked_iterable(iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

warn = set()

for chunk in chunked_iterable(list(qualified_players), 300):
    data = ','.join(chunk)
    headers = {'Content-Type': 'text/plain'}
    profiles = requests.post('https://lichess.org/api/users', data=data)
    for player in profiles.json():
        if not player.get('profile') or not player['profile'].get('country'):
            continue
        if player['profile']['country'] in ('RU', 'BY'):
            warn.add(player['username'])
    time.sleep(2)

print("The following players qualified so far:")
print(sorted(qualified_players, key=str.lower))
with open('qualified_players', 'w') as f:
    f.write('\n'.join(sorted(qualified_players, key=str.lower)))

print("The following players should be warned about RU/BY flags:")
print(sorted(warn, key=str.lower))
with open('warn_players', 'w') as f:
    f.write('\n'.join(sorted(warn, key=str.lower)))