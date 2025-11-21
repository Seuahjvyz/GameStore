GameStore — Scripts de esquema de base de datos

Archivos:
- `create_schema_postgres.sql` — Script SQL idempotente pensado para PostgreSQL (usa SERIAL, BYTEA y "ON CONFLICT" para semillas).
- `create_schema_sqlite.sql` — Script compatible con sqlite3 (usa AUTOINCREMENT, BLOB y funciones de fecha de SQLite).

Cómo usar

Postgres (psql):
```bash
# Reemplaza los valores por tu conexión
psql "postgresql://user:pass@host:5432/dbname" -f scripts/create_schema_postgres.sql
```

SQLite (sqlite3):
```bash
sqlite3 gamestore.db < scripts/create_schema_sqlite.sql
```

O usando SQLAlchemy desde la aplicación (recomendado para entornos de desarrollo):
- La app ya contiene una función `init_db_and_seed()` en `app.py` que llama a `db.create_all()` y añade datos de ejemplo.
- Para inicializar desde Python interactivo:
```bash
.venv/bin/python - <<'PY'
from app import init_db_and_seed
init_db_and_seed()
PY
```

Notas y recomendaciones
- Si usas PostgreSQL en producción, considera usar Alembic para migraciones en lugar de ejecutar el script directamente. El proyecto ya tiene scaffolding de Alembic en `alembic/`.
- El script es idempotente (usa `IF NOT EXISTS`), pero siempre revisa el resultado en ambientes con datos reales antes de ejecutar en producción.
- Los tipos elegidos siguen el mapeo de los modelos SQLAlchemy en `app.py` (BYTEA vs BLOB, DOUBLE PRECISION vs REAL).

Si quieres, puedo:
- Generar una revisión Alembic (`alembic revision --autogenerate`) basada en el estado actual del modelo para aplicar migraciones reproducibles.
- Añadir un pequeño script `scripts/init_db.py` que conecte con DATABASE_URL y aplique el script apropiado según el dialecto (Postgres vs SQLite).
