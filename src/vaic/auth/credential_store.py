"""Postgres-backed login credentials (FR-18): a real `account_credentials` table, bcrypt-hashed
passwords, verified against a username the caller actually types.

Patient accounts use their `patient_code` as `username` (per product decision) - a patient logs
in with the same code shown throughout the app, nothing extra to remember. Staff accounts use a
plain username. This is the credential store only: `Account` (`accounts.py`) never carries a
password hash, and nothing outside `verify_credentials`/`get_account_by_id` below ever sees one.

Table creation is lazy and idempotent (`checkfirst=True`, the SQLAlchemy default) - the first
caller in the process creates it if missing, exactly like `demo_seed.py`'s Patient/Resource seed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import Column, Text, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..state.postgres import get_engine, get_sessionmaker
from ..state.sql.models import Base
from .accounts import Account
from .roles import Role

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


class AccountCredentialRow(Base):
    __tablename__ = "account_credentials"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    patient_id = Column(PGUUID(as_uuid=True))
    resource_id = Column(PGUUID(as_uuid=True))


def _row_to_account(row: AccountCredentialRow) -> Account:
    return Account(
        id=row.id,
        username=row.username,
        role=Role(row.role),
        patient_id=row.patient_id,
        resource_id=row.resource_id,
    )


async def ensure_table(engine: AsyncEngine | None = None) -> None:
    async with (engine or get_engine()).begin() as conn:
        await conn.run_sync(
            lambda sync_conn: AccountCredentialRow.__table__.create(sync_conn, checkfirst=True)
        )


async def upsert_credential(
    *,
    id: UUID,
    username: str,
    password: str,
    role: Role,
    patient_id: UUID | None = None,
    resource_id: UUID | None = None,
    sessionmaker: async_sessionmaker[AsyncSession] | None = None,
) -> None:
    """Idempotent: re-seeding with the same `id` overwrites the row's fields (demo/dev only -
    never used to accept a real self-service registration)."""
    sm = sessionmaker or get_sessionmaker()
    async with sm() as session, session.begin():
        row = await session.get(AccountCredentialRow, id)
        password_hash = hash_password(password)
        if row is None:
            session.add(
                AccountCredentialRow(
                    id=id,
                    username=username,
                    password_hash=password_hash,
                    role=role.value,
                    patient_id=patient_id,
                    resource_id=resource_id,
                )
            )
        else:
            row.username = username
            row.password_hash = password_hash
            row.role = role.value
            row.patient_id = patient_id
            row.resource_id = resource_id


async def verify_credentials(
    username: str, password: str, sessionmaker: async_sessionmaker[AsyncSession] | None = None
) -> Account | None:
    """Return the `Account` if `username`/`password` match a stored credential, else `None` -
    never distinguishes "unknown username" from "wrong password" to the caller (no enumeration)."""
    sm = sessionmaker or get_sessionmaker()
    async with sm() as session:
        result = await session.execute(
            select(AccountCredentialRow).where(AccountCredentialRow.username == username)
        )
        row = result.scalar_one_or_none()
    if row is None or not _verify_password(password, row.password_hash):
        return None
    return _row_to_account(row)


async def get_account_by_id(
    account_id: UUID, sessionmaker: async_sessionmaker[AsyncSession] | None = None
) -> Account | None:
    sm = sessionmaker or get_sessionmaker()
    async with sm() as session:
        row = await session.get(AccountCredentialRow, account_id)
    return _row_to_account(row) if row is not None else None
