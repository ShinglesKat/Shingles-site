CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username TEXT CHECK (LENGTH(username) > 1 AND LENGTH(username) < 17),
    content TEXT NOT NULL CHECK (LENGTH(content) < 200),
    ip_address TEXT
);

CREATE TABLE pixels (
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    colour TEXT,
    PRIMARY KEY (x, y)
);

CREATE TABLE userinfo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK(LENGTH(username) >= 3 AND LENGTH(username) <= 16),
    password TEXT NOT NULL,
    creationTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    userType TEXT DEFAULT 'user',
    creationsIDs TEXT DEFAULT '[]'
);

CREATE TABLE userdrawings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    piece_name TEXT NOT NULL CHECK(LENGTH(piece_name) >= 3 AND LENGTH(piece_name) <= 30),
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    creationTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    private BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES userinfo(id),
    FOREIGN KEY (username) REFERENCES userinfo(username)
);

CREATE TABLE bannedIPs (
    ip TEXT PRIMARY KEY,
    reason TEXT,
    banned_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ban_duration TEXT NOT NULL,
    ban_expires_at TIMESTAMP NOT NULL
)