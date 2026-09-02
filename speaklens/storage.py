"""Keep sessions on disk so progress can be read across time (DEC-006).

What is worth comparing between sessions changed once recall was measured. The
original plan ranked error themes by frequency and called that the map, but at 27%
recall (DEC-024) such a ranking describes what the detector can see, not what the
speaker gets wrong. So mistakes are stored and listed, never ranked, while the
thing that actually trends is fluency — those numbers come from timings rather than
from anything a rule had to recognise.

The database holds transcripts of the user speaking and never leaves the machine.
It is gitignored for that reason.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "sessions.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT    NOT NULL,
    source        TEXT    NOT NULL,
    duration      REAL    NOT NULL,
    transcript    TEXT    NOT NULL,
    fluency       TEXT    NOT NULL,   -- json, so adding a metric needs no migration
    level         TEXT,               -- null when the sample was too small (DEC-023)
    content_words INTEGER NOT NULL,
    read_aloud    INTEGER NOT NULL,   -- 1 when the sample looked recited, so trends can skip it
    speaker       TEXT    NOT NULL DEFAULT ''   -- whose voice this was; '' means the owner
);

CREATE TABLE IF NOT EXISTS mistakes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    rule_id    TEXT    NOT NULL,
    theme_id   TEXT    NOT NULL,
    text       TEXT    NOT NULL,
    suggestion TEXT    NOT NULL,
    sentence   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS mistakes_by_session ON mistakes(session_id);
"""


@dataclass(frozen=True)
class StoredSession:
    id: int
    created_at: str
    source: str
    duration: float
    level: str | None
    read_aloud: bool
    speaker: str
    fluency: dict


def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    _migrate(connection)
    return connection


def _migrate(connection: sqlite3.Connection) -> None:
    """Add columns that CREATE TABLE IF NOT EXISTS cannot add to a table that exists.

    Databases predating a column are the normal case here, not an edge one: the
    file holds real sessions from before the column was thought of, and dropping it
    to get a clean schema would throw away the only measurements the thresholds are
    calibrated against.
    """
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(sessions)")}
    if "speaker" not in columns:
        with connection:
            connection.execute("ALTER TABLE sessions ADD COLUMN speaker TEXT NOT NULL DEFAULT ''")


def save(connection: sqlite3.Connection, *, source: str, duration: float,
         transcript: str, fluency, level, mistakes, speaker: str = "") -> int:
    """Store one run. Returns the new session id."""
    metrics = {
        "words_per_minute": fluency.words_per_minute,
        "mean_run_length": fluency.mean_run_length,
        "pauses_per_minute": fluency.pauses_per_minute,
        "longest_pause": fluency.longest_pause,
        "silence_ratio": fluency.silence_ratio,
        "fillers": fluency.fillers,
        "words": fluency.words,
    }
    with connection:
        cursor = connection.execute(
            "INSERT INTO sessions (created_at, source, duration, transcript, fluency,"
            " level, content_words, read_aloud, speaker) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                source,
                duration,
                transcript,
                json.dumps(metrics),
                level.level,
                level.content_words,
                int(fluency.looks_read_aloud),
                speaker,
            ),
        )
        session_id = int(cursor.lastrowid)
        connection.executemany(
            "INSERT INTO mistakes (session_id, rule_id, theme_id, text, suggestion,"
            " sentence) VALUES (?,?,?,?,?,?)",
            [(session_id, m.rule_id, m.theme_id, m.text, m.suggestion, m.sentence)
             for m in mistakes],
        )
    return session_id


def sessions(connection: sqlite3.Connection, spontaneous_only: bool = True,
             speaker: str | None = None) -> list[StoredSession]:
    """Sessions oldest first. Recited samples are excluded by default: their fluency
    numbers describe the reading, not the speaker (DEC-023)."""
    clauses, params = [], []
    if spontaneous_only:
        clauses.append("read_aloud = 0")
    if speaker is not None:
        clauses.append("speaker = ?")
        params.append(speaker)
    query = "SELECT * FROM sessions"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id"
    return [
        StoredSession(
            id=row["id"],
            created_at=row["created_at"],
            source=row["source"],
            duration=row["duration"],
            level=row["level"],
            read_aloud=bool(row["read_aloud"]),
            speaker=row["speaker"],
            fluency=json.loads(row["fluency"]),
        )
        for row in connection.execute(query, params)
    ]


def mistakes_by_theme(connection: sqlite3.Connection,
                      session_id: int | None = None) -> dict[str, list[sqlite3.Row]]:
    """Mistakes grouped by theme, in the order they were said.

    Grouped, never sorted by count: with the detector finding roughly one mistake
    in four, a frequency order would rank our own blind spots (DEC-024).
    """
    query = "SELECT * FROM mistakes"
    params: tuple = ()
    if session_id is not None:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY id"

    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in connection.execute(query, params):
        grouped.setdefault(row["theme_id"], []).append(row)
    return grouped


def fluency_trend(connection: sqlite3.Connection, metric: str,
                  speaker: str = "") -> list[tuple[str, float]]:
    """(date, value) for one fluency metric across one speaker's spontaneous sessions.

    Scoped to a speaker on purpose. The chart answers "am I improving", and a line
    that walks across several people answers nothing at all — which is exactly what
    it did the first time the app was handed to someone else.
    """
    return [
        (s.created_at[:10], s.fluency[metric])
        for s in sessions(connection, speaker=speaker)
        if metric in s.fluency
    ]
