"""Pool de conexiones a Postgres (Neon).

Se crea con open=False para que importar este módulo NO intente conectarse
(clave para que los tests corran sin base de datos). El pool se abre en el
lifespan de la app (ver main.py) y en producción/desarrollo real.
"""

import os

from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "")

pool = ConnectionPool(DATABASE_URL, min_size=0, max_size=4, open=False)
