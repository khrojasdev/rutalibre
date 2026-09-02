"""Pool de conexiones a Postgres (Neon)."""

import os
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from psycopg_pool import ConnectionPool


def _normalize(url: str) -> str:
    if not url:
        return url
    parts = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    if not any(k == "sslmode" for k, _ in query):
        query.append(("sslmode", "require"))
    return urlunparse(parts._replace(query=urlencode(query)))


DATABASE_URL = _normalize(os.getenv("DATABASE_URL", ""))

pool = ConnectionPool(
    DATABASE_URL,
    min_size=0,
    max_size=4,
    max_idle=60,
    check=ConnectionPool.check_connection,
    open=False,
)
