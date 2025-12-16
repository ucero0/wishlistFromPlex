"""Persistence migrations package.

This package contains all Alembic database migration files and configuration.

Structure:
- alembic/          - Alembic migration scripts and environment
  - env.py          - Alembic environment configuration
  - versions/       - Migration version files
- alembic.ini        - Alembic configuration file

Usage:
To run migrations from the project root:
    alembic -c app/infrastructure/persistence/migrations/alembic.ini upgrade head

Or create a symlink/alias for convenience.
"""
