"""Tiny SQLite phrasebook. Single local user for now (no auth)."""

import json
import sqlite3
from contextlib import contextmanager

from .config import settings

DB_PATH = settings.data_dir / "softutter.db"
STATUSES = ("new", "echo", "own")
SOUND_OUTCOMES = ("seen", "clear", "care")


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    with db() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS phrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                target TEXT NOT NULL,
                meaning TEXT DEFAULT '',
                reading TEXT DEFAULT '',
                ipa TEXT DEFAULT '',
                status TEXT DEFAULT 'new',
                payload TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS sound_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                key TEXT NOT NULL,
                title TEXT NOT NULL,
                symbol TEXT DEFAULT '',
                tag TEXT DEFAULT 'care',
                tip TEXT DEFAULT '',
                outcome TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["payload"] = json.loads(d.get("payload") or "{}")
    return d


def list_phrases(language: str | None = None) -> list[dict]:
    with db() as c:
        if language:
            rows = c.execute(
                "SELECT * FROM phrases WHERE language=? ORDER BY id DESC", (language,)
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM phrases ORDER BY id DESC").fetchall()
    return [_row(r) for r in rows]


def add_phrase(p: dict) -> dict:
    with db() as c:
        existing = c.execute(
            "SELECT * FROM phrases WHERE language=? AND target=?",
            (p["language"], p["target"]),
        ).fetchone()
        if existing:
            return _row(existing)
        cur = c.execute(
            "INSERT INTO phrases (language, target, meaning, reading, ipa, payload) VALUES (?,?,?,?,?,?)",
            (
                p["language"],
                p["target"],
                p.get("meaning", ""),
                p.get("reading", ""),
                p.get("ipa", ""),
                json.dumps(p.get("payload", {}), ensure_ascii=False),
            ),
        )
        row = c.execute("SELECT * FROM phrases WHERE id=?", (cur.lastrowid,)).fetchone()
    return _row(row)


def set_status(phrase_id: int, status: str) -> dict | None:
    with db() as c:
        c.execute("UPDATE phrases SET status=? WHERE id=?", (status, phrase_id))
        row = c.execute("SELECT * FROM phrases WHERE id=?", (phrase_id,)).fetchone()
    return _row(row) if row else None


def delete_phrase(phrase_id: int) -> None:
    with db() as c:
        c.execute("DELETE FROM phrases WHERE id=?", (phrase_id,))


# ---------- My sounds ----------


def sound_key(title: str) -> str:
    return " ".join(title.lower().split())


def add_sound_events(language: str, events: list[dict]) -> None:
    rows = [
        (
            language,
            sound_key(e["title"]),
            e["title"],
            e.get("symbol", ""),
            e.get("tag", "care"),
            e.get("tip", ""),
            e["outcome"],
        )
        for e in events
    ]
    with db() as c:
        c.executemany(
            "INSERT INTO sound_events (language, key, title, symbol, tag, tip, outcome) VALUES (?,?,?,?,?,?,?)",
            rows,
        )


def sound_status(outcomes: list[str]) -> str:
    """working: a recent attempt needed another go. steady: recent attempts all clear."""
    last = outcomes[-3:]
    if "care" in last:
        return "working"
    if len(outcomes) >= 2 and all(o == "clear" for o in last):
        return "steady"
    return "new"


def list_sounds(language: str | None = None) -> list[dict]:
    with db() as c:
        if language:
            rows = c.execute(
                "SELECT * FROM sound_events WHERE language=? ORDER BY id", (language,)
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM sound_events ORDER BY id").fetchall()
    groups: dict[tuple, dict] = {}
    for r in rows:
        g = groups.setdefault(
            (r["language"], r["key"]),
            {"language": r["language"], "key": r["key"], "seen": 0, "outcomes": []},
        )
        g.update(title=r["title"], symbol=r["symbol"], tag=r["tag"], tip=r["tip"], last_at=r["created_at"])
        if r["outcome"] == "seen":
            g["seen"] += 1
        else:
            g["outcomes"].append(r["outcome"])
    out = []
    for g in groups.values():
        o = g.pop("outcomes")
        g.update(
            attempts=len(o),
            clear=o.count("clear"),
            care=o.count("care"),
            history=o[-8:],
            status=sound_status(o),
        )
        out.append(g)
    out.sort(key=lambda g: g["last_at"], reverse=True)
    order = {"working": 0, "new": 1, "steady": 2}
    out.sort(key=lambda g: order[g["status"]])  # stable: newest first within a status
    return out
