Alembic migration helper

This repository includes a minimal Alembic scaffolding under `alembic/` and a basic `alembic.ini`.

Quickstart (development):

1. Install requirements (in your virtualenv):

   pip install -r requirements.txt

2. Create a new revision (autogenerate) and upgrade:

   # create a new revision using autogenerate
   alembic revision --autogenerate -m "initial"

   # apply migrations
   alembic upgrade head

Notes:
- The env.py reads the database URL from the Flask `app.config['SQLALCHEMY_DATABASE_URI']` so ensure your environment variables (e.g., DATABASE_URL) are set before running alembic commands.
- If Alembic complains about the template location, ensure you run commands from the repository root where `alembic.ini` resides.
- For production, review generated migration scripts before applying them.
