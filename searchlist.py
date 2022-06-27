#!/usr/bin/env python3
import json
import os

import regex as re

from db import Database

database = Database('out/gcdb.sqlite3')


def to_item(row):
    name, image_id = row
    key = re.sub(r'[^\p{L}\p{N}]+', '.', str(name).lower()).strip('.')
    return key, image_id, name


rows = sorted(map(to_item, database.execute('SELECT name, image_id FROM games '
                                            'INNER JOIN covers c on games.id = c.game')),
              key=lambda item: item[0])
buckets = {}

for (key, image_id, name) in rows:
    if not len(key):
        continue
    bucket = key.split('.')[0][:2]
    if not re.fullmatch(r'[\da-z]+', bucket):
        bucket = '@'
    items = buckets.get(bucket, None)
    if not items:
        items = {}
        buckets[bucket] = items
    items[key] = {'hash': image_id, 'name': name}

os.makedirs('out/buckets', exist_ok=True)

for bucket in buckets:
    with open(f'out/buckets/{bucket}.json', mode='w', encoding='utf-8') as f:
        json.dump(buckets[bucket], f)
