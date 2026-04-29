"""csp.persistence — DuckDB-Schicht (Slice 6).

`db.connection(settings)` ist der einzige Entry-Point; öffnet eine
`duckdb.DuckDBPyConnection`, wendet Migrationen an, gibt sie als Context-Manager
zurück. Aufruf-Codes (`lifecycle_api.py`) öffnen pro Public-Funktion eine
neue Connection — DuckDB ist in-Process, kostenlos zu öffnen.
"""

from csp.persistence.db import connection

__all__ = ["connection"]
