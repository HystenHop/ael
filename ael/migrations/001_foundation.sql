CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'almoxarife', 'solicitante', 'aprovador')),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE materials (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK(length(code) BETWEEN 2 AND 30),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 100),
    category TEXT NOT NULL CHECK(category IN ('EPI', 'Ferramentas', 'Consumíveis', 'Peças', 'Outros')),
    unit TEXT NOT NULL CHECK(unit IN ('UN', 'PAR', 'CX', 'KG', 'L', 'M')),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK(length(code) BETWEEN 2 AND 30),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 100),
    address TEXT NOT NULL CHECK(length(trim(address)) BETWEEN 2 AND 160),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER NOT NULL REFERENCES users(id),
    entity TEXT NOT NULL CHECK(entity IN ('materials', 'locations')),
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('create', 'update', 'deactivate', 'reactivate')),
    before_json TEXT,
    after_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
