--
-- Файл сгенерирован с помощью SQLiteStudio v3.4.4 в Ср авг 2 03:06:22 2023
--
-- Использованная кодировка текста: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: bytedata
CREATE TABLE IF NOT EXISTS bytedata (
    id    TEXT PRIMARY KEY
               REFERENCES files (id) ON DELETE CASCADE
               NOT NULL,
    bytes BLOB
);


-- Таблица: events
CREATE TABLE IF NOT EXISTS events (
    id         TEXT    PRIMARY KEY
                       NOT NULL
                       UNIQUE,
    time       TEXT    NOT NULL
                       DEFAULT ('~'),
    code       TEXT    NOT NULL
                       DEFAULT ('test'),
    regularity REAL,
    exceptions TEXT,
    daemon     INTEGER DEFAULT (0) 
                       NOT NULL,
    done       INTEGER DEFAULT (0),
    active     INTEGER DEFAULT (1) 
);


-- Таблица: files
CREATE TABLE IF NOT EXISTS files (
    id     TEXT PRIMARY KEY,
    tg_id  TEXT,
    name   TEXT,
    folder TEXT
);


-- Таблица: logs
CREATE TABLE IF NOT EXISTS logs (
    id     TEXT PRIMARY KEY
                UNIQUE
                NOT NULL,
    time   TEXT NOT NULL,
    log    TEXT NOT NULL,
    anchor TEXT NOT NULL
                REFERENCES orders (_logging) ON DELETE CASCADE
                                             ON UPDATE CASCADE
);


-- Таблица: orders
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY
                            NOT NULL
                            UNIQUE,
    customer        INTEGER REFERENCES profiles (id) ON DELETE SET NULL
                                                     ON UPDATE CASCADE,
    status          TEXT    NOT NULL
                            DEFAULT ('created'),
    _status_updated TEXT,
    type            TEXT,
    master          INTEGER REFERENCES profiles (id) ON DELETE SET NULL
                                                     ON UPDATE CASCADE,
    description     TEXT    DEFAULT (''),
    reference       TEXT    UNIQUE,
    product         TEXT    UNIQUE,
    deadline        TEXT    DEFAULT ('~'),
    _logging        TEXT    UNIQUE,
    _prev           INTEGER REFERENCES orders (id) ON UPDATE CASCADE
);


-- Таблица: profiles
CREATE TABLE IF NOT EXISTS profiles (
    id            INTEGER PRIMARY KEY
                          UNIQUE
                          NOT NULL,
    username      TEXT,
    first_name    TEXT,
    last_name     TEXT,
    language_code TEXT    NOT NULL
                          DEFAULT ('en'),
    status        TEXT    NOT NULL
                          DEFAULT ('newcomer'),
    reputation    REAL    NOT NULL
                          DEFAULT (0.0),
    registered    TEXT,
    nav           TEXT    NOT NULL
                          DEFAULT ('main_menu'),
    sys_lang      INTEGER DEFAULT (0) 
                          NOT NULL,
    filters       TEXT    DEFAULT ('advertising/patch_note/other'),
    _unban_date   TEXT
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
