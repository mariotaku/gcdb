CREATE TABLE games
(
    id         int primary key on conflict ignore,
    name       text not null on conflict replace,
    cover      int  not null on conflict replace,
    updated_at int  not null on conflict replace
);

CREATE INDEX game_names_idx ON games (name);

CREATE TABLE covers
(
    id       int primary key on conflict ignore,
    game     int  not null on conflict replace,
    width    int  not null on conflict replace,
    height   int  not null on conflict replace,
    image_id text not null on conflict replace,
    foreign key (game) references games (id)
);

CREATE INDEX cover_game_idx ON covers (game);