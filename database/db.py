from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from database.models import Base
import logging

logger = logging.getLogger("sherlock_vision.db")

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        logger.info("Initializing database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized.")

async def get_session() -> AsyncSession:
    """Dependency to get the database session."""
    async with AsyncSessionLocal() as session:
        yield session
