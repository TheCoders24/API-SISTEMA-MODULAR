# database/UnitOfWork.py
from sqlalchemy.ext.asyncio import AsyncSession
from .session import async_session
from .Mongodb_Connection import mongo_manager

class UnitOfWork:
    """
    Unidad de trabajo para manejar transacciones SQL y acceso a MongoDB.
    Uso recomendado:
        async with UnitOfWork() as uow:
            # usar uow.session y uow.mongo
    """

    def __init__(self):
        self.session: AsyncSession | None = None
        self.mongo = None

    async def __aenter__(self):
        # Crear sesión SQL usando el async_sessionmaker vinculado al engine
        self.session = async_session()
        # Conectar a Mongo
        self.mongo = mongo_manager.db
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type:
                    await self.session.rollback()
                else:
                    await self.session.commit()
            finally:
                await self.session.close()

    # Opcional: helper para usar transaction
    async def transaction(self):
        async with self as uow:
            yield uow


"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @asynccontextmanager
    async def transaction(self):
        try:
            await self.db.begin()  # Inicia la transacción
            yield
            await self.db.commit()  # Commit si no hay error
        except Exception:
            await self.db.rollback()  # Rollback si hay error
            raise
        finally:
            await self.db.close()  # Cierra la sesión
"""

"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncIterator, Optional

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
       
        if self._transaction is not None:
            raise RuntimeError("Ya hay una transacción en curso")
        
        self._transaction = await self.session.begin()
        try:
            yield
            await self.session.commit()
        except Exception:
            await self.rollback()
            raise
        finally:
            self._transaction = None
            # No cerramos la sesión aquí para permitir su reutilización

    async def commit(self):
        
        if self._transaction is None:
            raise RuntimeError("No hay transacción activa para confirmar")
        await self.session.commit()
        self._transaction = None

    async def rollback(self):
        
        if self._transaction is None:
            raise RuntimeError("No hay transacción activa para revertir")
        await self.session.rollback()
        self._transaction = None

    async def close(self):
        
        if self._transaction is not None:
            await self.rollback()
        await self.session.close()
"""




"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None

    @asynccontextmanager
    async def transaction(self):
        if self._transaction is not None:
            raise RuntimeError("Transaction already in progress")
        
        self._transaction = await self.session.begin()
        try:
            yield
            await self._transaction.commit()
        except Exception:
            await self._transaction.rollback()
            raise
        finally:
            self._transaction = None

    async def rollback(self):
        if self._transaction is not None:
            await self._transaction.rollback()
            self._transaction = None
"""