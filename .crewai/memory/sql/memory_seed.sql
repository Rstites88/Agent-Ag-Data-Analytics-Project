-- CrewAI review memory seed (generated)
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS learned_patterns (
    id TEXT PRIMARY KEY,
    observation TEXT NOT NULL,
    confidence REAL NOT NULL,
    source TEXT NOT NULL,
    learned_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS suppressions (
    id TEXT PRIMARY KEY,
    pattern TEXT NOT NULL,
    file_glob TEXT NOT NULL,
    reason TEXT NOT NULL,
    added_by TEXT NOT NULL,
    added_date TEXT NOT NULL,
    expires TEXT NOT NULL,
    active INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS review_history (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_reviews INTEGER NOT NULL,
    last_review TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_history_trend (
    idx INTEGER PRIMARY KEY,
    pr TEXT NOT NULL,
    findings INTEGER NOT NULL,
    date TEXT NOT NULL
);
DELETE FROM learned_patterns;
DELETE FROM suppressions;
DELETE FROM review_history;
DELETE FROM review_history_trend;
INSERT INTO learned_patterns (
    id, observation, confidence, source, learned_date
) VALUES (
    'pat-001',
    'Do not flag placeholder secrets in .env.example files when values are clearly fake examples and no real credentials are present.',
    1.0,
    'maintainer-policy',
    '2026-02-15'
);
INSERT INTO suppressions (
    id, pattern, file_glob, reason, added_by, added_date, expires, active
) VALUES (
    'example-001',
    'hardcoded URL in example file',
    'agentic/mermaid_diagrams/*.md',
    'These are intentional documentation examples, not production code',
    'template',
    '2026-02-13',
    'None',
    1
);
INSERT INTO suppressions (
    id, pattern, file_glob, reason, added_by, added_date, expires, active
) VALUES (
    'sup-001',
    'placeholder api keys and tokens',
    '*.env.example',
    'Placeholder credentials in .env.example templates are acceptable when they are clearly fake and no real secrets are committed.',
    'memory-cli-bootstrap',
    '2026-02-15',
    'None',
    1
);
INSERT INTO review_history (id, total_reviews, last_review) VALUES (1, 0, '');
COMMIT;
