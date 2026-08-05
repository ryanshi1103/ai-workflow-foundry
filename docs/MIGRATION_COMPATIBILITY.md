# Migration compatibility

## Stable interfaces

The Feedback Intelligence rename does not remove the original runtime surface.
Existing launchers may continue to run `streamlit run app.py` or `scripts/run.sh`.
Existing Python callers may continue to import `src.*`; those names alias the
canonical `feedback_intelligence.*` module objects and are deprecated, not copied.

The following interfaces are deliberately preserved:

- `APP_*`, `DEEPSEEK_*`, and `APIFY_*` environment variables
- `sqlite:///data/social_monitor.db` as the default database URL
- existing table and column names
- Streamlit widget keys and page imports
- CSV header order and UTF-8-SIG encoding
- JSON export shape

## Database procedure

1. Back up the SQLite database and any WAL/SHM companions while the application
   is stopped.
2. Start the updated application or call
   `feedback_intelligence.migrations.run_migrations()`.
3. The current ORM creates missing tables; additive migration steps add only
   missing columns and indexes.
4. Re-running the same migration is a no-op.
5. If a migration raises, treat the upgrade as failed and restore the external
   backup before retrying. The migration does not suppress failures.

An empty database is initialized directly at the latest schema. The automated
suite also constructs an old schema, preserves its rows, runs the migration
twice, validates a different current working directory, and confirms that
`sqlite:///:memory:` never becomes a disk file.

## Rollback

Code rollback is a normal Git branch reset or revert performed by the operator.
Schema changes are additive, so an older application can retain the upgraded
database after a compatibility review. For an exact schema rollback, restore the
pre-upgrade SQLite backup; no automated destructive down-migration is provided.

## Deprecation

`src.*`, `APP_DB_URL`, and the `social_monitor.db` filename have no removal date.
Any future removal requires a separate release, a warning period, and explicit
upgrade documentation. Remote GitHub rename and release operations require human
authorization and are not part of this local migration.
