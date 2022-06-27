import dataclasses
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Iterable

import requests as requests
import yaml
from ratelimiter import RateLimiter


@dataclass
class Game:
    id: int
    name: int
    cover: str
    updated_at: int


@dataclass
class Cover:
    id: int
    game: int
    image_id: str
    width: int = 0
    height: int = 0


@dataclass
class ClientCredential:
    client_id: str
    client_secret: str


@dataclass
class AccessToken:
    access_token: str
    expires_in: int
    token_type: str

    def __post_init__(self):
        self.expires_at = datetime.now() + timedelta(seconds=self.expires_in)

    def expired(self) -> bool:
        return datetime.now() >= self.expires_at


class Client:
    _access_token: Optional[AccessToken] = None
    _rate_limiter = RateLimiter(max_calls=4, period=1.0)

    def __init__(self):
        if 'IGDB_CLIENT_ID' in os.environ and 'IGDB_CLIENT_SECRET' in os.environ:
            self.creds = ClientCredential(os.environ['IGDB_CLIENT_ID'], os.environ['IGDB_CLIENT_SECRET'])
        else:
            with open('credential.yaml') as f:
                self.creds = ClientCredential(**yaml.safe_load(f))

    def get_games(self, after: int or None = None, limit: int = 500, updated_at: int = 0) -> List[Game]:
        fields = map(lambda field: field.name, dataclasses.fields(Game))
        where = f'version_parent = null & cover != null'
        if after:
            where = f'{where} & id > {after}'
        if updated_at > 0:
            where = f'{where} & updated_at > {updated_at}'
        with self._rate_limiter:
            resp = requests.post('https://api.igdb.com/v4/games', headers=self.authorization_header(),
                                 data=f'fields {",".join(fields)}; where {where}; limit {limit}; sort id;')
        if not resp.ok:
            raise Exception(resp.json())
        return list(map(lambda item: Game(**item), resp.json()))

    def get_covers(self, cover_ids: Iterable[str]):
        fields = map(lambda field: field.name, dataclasses.fields(Cover))
        ids = list(cover_ids)
        with self._rate_limiter:
            resp = requests.post('https://api.igdb.com/v4/covers', headers=self.authorization_header(),
                                 data=f'fields {",".join(fields)}; where id = ({",".join(ids)}); '
                                      f'limit {len(ids)};')
        if not resp.ok:
            raise Exception(resp.json())
        return list(map(lambda item: Cover(**item), resp.json()))

    def authorization_header(self):
        token = self.obtain_access_token().access_token
        return {
            'Authorization': f'Bearer {token}',
            'Client-ID': self.creds.client_id
        }

    def obtain_access_token(self) -> AccessToken:
        if not self._access_token or self._access_token.expired():
            resp = requests.post('https://id.twitch.tv/oauth2/token',
                                 params=dataclasses.asdict(self.creds) | {'grant_type': 'client_credentials'})
            self._access_token = AccessToken(**resp.json())
        return self._access_token
