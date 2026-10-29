from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.database.models import Base

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def _migrate_sqlite_exponent(sync_conn) -> None:
    """Rebuild keys.exponent as TEXT when an older SQLite file used INTEGER.

    Wiener public exponents exceed 2^63-1. SQLite INTEGER affinity stores those
    as REAL and drops bits, so the continued-fraction attack misses.
    """
    if sync_conn.dialect.name != "sqlite":
        return
    info = sync_conn.exec_driver_sql("PRAGMA table_info(keys)").fetchall()
    if not info:
        return
    exponent = next((row for row in info if row[1] == "exponent"), None)
    if exponent is None or "INT" not in str(exponent[2]).upper():
        return
    cols = [row[1] for row in info]
    col_sql = ", ".join(cols)
    sync_conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
    sync_conn.exec_driver_sql("ALTER TABLE keys RENAME TO keys_int_exponent")
    indexes = sync_conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='keys_int_exponent'"
    ).fetchall()
    for (index_name,) in indexes:
        if index_name and not str(index_name).startswith("sqlite_"):
            sync_conn.exec_driver_sql(f'DROP INDEX IF EXISTS "{index_name}"')
    Base.metadata.tables["keys"].create(sync_conn)
    sync_conn.exec_driver_sql(
        f"INSERT INTO keys ({col_sql}) SELECT {col_sql} FROM keys_int_exponent"
    )
    sync_conn.exec_driver_sql(
        "DELETE FROM keys WHERE CAST(exponent AS TEXT) LIKE '%.%' OR CAST(exponent AS TEXT) LIKE '%e%'"
    )
    sync_conn.exec_driver_sql("DROP TABLE keys_int_exponent")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_migrate_sqlite_exponent)
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
