"""`ideas`-Tabelle CRUD (Slice 6).

Persistiert `Idea`-Snapshots als JSON (volle Treue für `csp.get_idea` / 6-Monats-
Reproduktion, NFR17) plus denormalisierte Spalten für effiziente Filterung in
`csp.list_ideas` (`ticker`, `as_of`, `pflichtregeln_passed`, `bypassed_count`,
`region`, `data_freshness`, `annualized_yield_pct`).

UUIDs werden vom Caller (`lifecycle_api.log_idea`) übergeben — das hält die
Idempotenz-Verantwortung dort, wo die Business-Logik lebt.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import duckdb

from csp.models.idea import Idea


def insert_idea(con: duckdb.DuckDBPyConnection, *, idea_id: str, idea: Idea) -> None:
    """`INSERT OR REPLACE` einer Idea — idempotent same-day-Reruns (NFR12)."""
    con.execute(
        """
        INSERT OR REPLACE INTO ideas (
            idea_id, ticker, as_of, pflichtregeln_passed, bypassed_count,
            region, data_freshness, annualized_yield_pct, idea_json, inserted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            idea_id,
            idea.ticker,
            idea.as_of,
            idea.pflichtregeln_passed,
            len(idea.bypassed_rules),
            idea.region,
            idea.data_freshness,
            idea.annualized_yield_pct,
            idea.model_dump_json(),
            datetime.now(UTC),
        ],
    )


def get_idea_by_id(con: duckdb.DuckDBPyConnection, idea_id: str) -> Idea | None:
    """Lädt einen Idea-Snapshot aus dem `idea_json`-Feld zurück."""
    row = con.execute(
        "SELECT idea_json FROM ideas WHERE idea_id = ?",
        [idea_id],
    ).fetchone()
    if row is None:
        return None
    return Idea.model_validate_json(row[0])


def list_ideas(
    con: duckdb.DuckDBPyConnection,
    *,
    since: date | None = None,
    overrides_only: bool = False,
) -> list[Idea]:
    """Liefert alle Ideas — optional zeit- und override-gefiltert.

    Sortierung: `as_of` DESC, `ticker` ASC — neueste zuerst, deterministisch
    bei gleichem Datum.
    """
    sql = "SELECT idea_json FROM ideas"
    where: list[str] = []
    params: list[object] = []
    if since is not None:
        where.append("as_of >= ?")
        params.append(since)
    if overrides_only:
        where.append("bypassed_count > 0")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY as_of DESC, ticker ASC"
    rows = con.execute(sql, params).fetchall()
    return [Idea.model_validate_json(row[0]) for row in rows]
