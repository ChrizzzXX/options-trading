"""DuckDB-Connection-Helper + Migrations-Runner (Slice 6).

`connection(settings)` ist der einzige Entry-Point: öffnet eine DuckDB-Datei
nach `Settings.duckdb_path`, wendet alle ausstehenden Migrationen an, gibt sie
als Context-Manager zurück (mit `__exit__` schließt sie sauber).

Migrationen liegen in `src/csp/persistence/migrations/NNN_<name>.sql`. Der
Runner liest die Dateien, sortiert sie numerisch, prüft `_migrations.version`
gegen jede Datei und wendet die fehlenden an. Das ist das einzige Schreib-API,
das DDL ausführt — alle `lifecycle_api`-Funktionen tun nur DML.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from csp.config import Settings

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_MIGRATION_FILENAME_RE = re.compile(r"^(\d+)_.+\.sql$")


def _list_migrations() -> list[tuple[int, Path]]:
    """Zählt alle `NNN_<name>.sql`-Dateien auf, sortiert nach Versions-Zahl."""
    found: list[tuple[int, Path]] = []
    for p in _MIGRATIONS_DIR.iterdir():
        if not p.is_file():
            continue
        m = _MIGRATION_FILENAME_RE.match(p.name)
        if m is None:
            continue
        found.append((int(m.group(1)), p))
    found.sort(key=lambda pair: pair[0])
    return found


def _ensure_migrations_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL
        )
        """
    )


def _applied_versions(con: duckdb.DuckDBPyConnection) -> set[int]:
    rows = con.execute("SELECT version FROM _migrations").fetchall()
    return {int(row[0]) for row in rows}


def _strip_sql_line_comments(sql: str) -> str:
    """Entfernt `--`-Zeilenkommentare. SQL-Strings dürfen `--` nicht enthalten —
    diese Migrations sind reine DDL ohne Literale, daher safe."""
    cleaned_lines: list[str] = []
    for line in sql.splitlines():
        # `--` außerhalb von Strings → Rest der Zeile ist Kommentar.
        comment_idx = line.find("--")
        if comment_idx >= 0:
            cleaned_lines.append(line[:comment_idx])
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _apply_migrations(con: duckdb.DuckDBPyConnection) -> None:
    _ensure_migrations_table(con)
    applied = _applied_versions(con)
    now = datetime.now(UTC)
    for version, path in _list_migrations():
        if version in applied:
            continue
        raw_sql = path.read_text(encoding="utf-8")
        # Kommentare strippen, damit `;` in einem `--`-Kommentar den Parser nicht
        # in zwei Statements aufteilt.
        sql = _strip_sql_line_comments(raw_sql)
        # DuckDB unterstützt `executemany` nicht für DDL — wir teilen am `;`.
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            con.execute(stmt)
        con.execute(
            "INSERT INTO _migrations (version, name, applied_at) VALUES (?, ?, ?)",
            [version, path.name, now],
        )


@contextmanager
def connection(settings: Settings) -> Iterator[duckdb.DuckDBPyConnection]:
    """Öffnet eine DuckDB-Connection nach `Settings.duckdb_path`.

    - Erstellt das Verzeichnis falls nötig (außer bei `:memory:`).
    - Wendet ausstehende Migrationen an.
    - Schließt die Connection beim Verlassen des `with`-Blocks.
    """
    db_path = settings.duckdb_path
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        _apply_migrations(con)
        yield con
    finally:
        con.close()
