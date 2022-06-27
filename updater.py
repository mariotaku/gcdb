#!/usr/bin/env python3
import os
from concurrent.futures import ThreadPoolExecutor
from os import path
from packaging import version
import requests

from api import Client
from db import Database, Schema

client = Client()
schema = Schema(1, {
    1: 'migrations/1_base.sql'
})

database = Database('out/gcdb.sqlite3', schema)


def fetch_games():
    updated_at, = database.execute('SELECT MAX(updated_at) FROM games').fetchone()
    begin = None
    if not updated_at:
        updated_at = 0
    while True:
        if begin:
            print(f'Fetching games after {begin}.')
        else:
            print(f'Fetching games (first page)')
        games = client.get_games(begin, updated_at=updated_at)
        if len(games) == 0:
            break
        values = list(map(lambda game: (game.id, game.name, game.cover, game.updated_at), games))
        cur = database.cursor()
        cur.executemany('INSERT INTO games(id, name, cover, updated_at) VALUES (?, ?, ?, ?)', values)
        database.commit()
        begin = games[-1].id


def fetch_covers():
    begin = 0
    while True:
        if begin:
            print(f'Fetching covers after {begin}.')
        else:
            print(f'Fetching covers (first page)')
        rows = database.execute(f'SELECT id, cover FROM games WHERE id > {begin} AND '
                                f'cover NOT IN(SELECT id FROM covers) '
                                f'ORDER BY id LIMIT 500').fetchall()
        if len(rows) == 0:
            break
        covers = client.get_covers(map(lambda row: str(row[1]), rows))
        values = list(map(lambda cover: (cover.id, cover.game, cover.width, cover.height, cover.image_id), covers))
        cur = database.cursor()
        cur.executemany('INSERT INTO covers(id, game, width, height, image_id) VALUES (?, ?, ?, ?, ?)', values)
        database.commit()
        begin = int(rows[-1][0])


def fetch_assets():
    executor = ThreadPoolExecutor(40)

    def download_image(row: (str,)):
        img, = row
        if not path.exists(f'assets/{img}.png'):
            with open(f'assets/{img}.png', 'wb') as f:
                with requests.get(f'https://images.igdb.com/igdb/image/upload/t_cover_big/{img}.png') as resp:
                    if resp.ok:
                        f.write(resp.content)
        if not path.exists(f'assets/{img}@2x.png'):
            with open(f'assets/{img}@2x.png', 'wb') as f:
                with requests.get(f'https://images.igdb.com/igdb/image/upload/t_cover_big_2x/{img}.png') as resp:
                    if resp.ok:
                        f.write(resp.content)

    try:
        executor.map(download_image,
                     database.execute('SELECT image_id FROM covers WHERE width > 0 AND height > 0').fetchall())
    finally:
        executor.shutdown()


if __name__ == '__main__':
    v, = database.execute('SELECT sqlite_version()').fetchone()
    v_wants = '3.24'
    if version.parse(v) < version.parse(v_wants):
        print(f'SQLite {v_wants} and above is required! (You have {v})')
        exit(1)
    fetch_games()
    fetch_covers()
