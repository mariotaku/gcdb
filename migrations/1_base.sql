CREATE TABLE games
(
    id    int primary key,
    name  int,
    cover text
);

CREATE INDEX game_names_idx ON games (name);

CREATE TABLE covers
(
    id       int primary key,
    game     int,
    width    int,
    height   int,
    image_id text,
    foreign key (game) references games (id)
);

CREATE INDEX cover_game_idx ON covers (game);