"""
Database Configuration and Connection Management

Provides SQLAlchemy database setup, connection pooling, and session management.
Includes transaction management and connection pool monitoring.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from utils.logger import setup_logger
from utils.metrics import database_connection_pool_size, database_errors_total

logger = setup_logger(__name__)
config = Config()

# Create declarative base for all models
Base = declarative_base()

# Database engine configuration
def create_db_engine():
    """
    Create SQLAlchemy database engine with optimized connection pooling.
    
    Connection pooling configuration:
    - SQLite: StaticPool for in-memory, QueuePool for file-based
    - PostgreSQL/MySQL: QueuePool with pre-ping for connection validation
    - Pool size: 10 connections (configurable via DATABASE_POOL_SIZE)
    - Max overflow: 20 additional connections (configurable via DATABASE_MAX_OVERFLOW)
    - Pre-ping: Validates connections before use to detect stale connections
    
    Returns:
        SQLAlchemy Engine instance with optimized connection pooling
    """
    database_url = config.DATABASE_URL
    pool_size = getattr(config, 'DATABASE_POOL_SIZE', 10)
    max_overflow = getattr(config, 'DATABASE_MAX_OVERFLOW', 20)
    
    logger.info(f"Creating database engine: {database_url}")
    logger.info(f"Connection pool configuration: pool_size={pool_size}, max_overflow={max_overflow}")
    
    # Determine pool class based on database type
    if 'sqlite' in database_url:
        # SQLite uses StaticPool for in-memory databases
        pool_class = StaticPool if ':memory:' in database_url else QueuePool
        engine = create_engine(
            database_url,
            connect_args={'check_same_thread': False},
            poolclass=pool_class,
            echo=config.DEBUG
        )
    else:
        # PostgreSQL and other databases use QueuePool with optimized settings
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=config.DEBUG
        )
    
    # Setup event listeners for connection pool monitoring and error handling
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log database connections and update metrics"""
        logger.debug("Database connection established")
        try:
            database_connection_pool_size.set(engine.pool.size())
        except Exception as e:
            logger.debug(f"Could not update pool size metric: {str(e)}")
    
    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log database disconnections"""
        logger.debug("Database connection closed")
    
    @event.listens_for(engine, "detach")
    def receive_detach(dbapi_conn, connection_record):
        """Log connection detachment"""
        logger.debug("Database connection detached")
    
    return engine


# Create engine and session factory
engine = create_db_engine()
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
))


def get_db_session():
    """
    Get a database session.
    
    Returns a new session instance that should be used within a transaction context.
    The session will be automatically managed by the transaction context manager.
    
    Returns:
        SQLAlchemy Session instance
    """
    return SessionLocal()


def get_session():
    """
    Alias for get_db_session() for convenience.
    
    Returns:
        SQLAlchemy Session instance
    """
    return get_db_session()


def init_db():
    """
    Initialize database by creating all tables
    
    This should be called once at application startup
    """
    try:
        logger.info("Initializing database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        database_errors_total.labels(error_type="initialization").inc()
        raise


def drop_db():
    """
    Drop all database tables
    
    WARNING: This will delete all data. Use only for testing.
    """
    try:
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        database_errors_total.labels(error_type="drop").inc()
        raise


def close_db():
    """
    Close database connection.
    
    This should be called at application shutdown to properly close
    all connections in the pool and release resources.
    """
    try:
        logger.info("Closing database connection")
        SessionLocal.remove()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database connection: {str(e)}")
        database_errors_total.labels(error_type="close").inc()
        raise


def get_connection_pool_info():
    """
    Get information about the current connection pool status.
    
    Returns:
        Dictionary with pool information including size, overflow, and active connections
    """
    pool = engine.pool
    info = {
        "pool_class": pool.__class__.__name__,
        "pool_size": getattr(pool, 'pool_size', None),
        "max_overflow": getattr(pool, 'max_overflow', None),
    }
    logger.debug(f"Connection pool info: {info}")
    return info


def validate_connection():
    """
    Validate that the database connection is working.
    
    Attempts to execute a simple query to verify connectivity.
    
    Returns:
        True if connection is valid, False otherwise
        
    Raises:
        SQLAlchemyError: If connection validation fails
    """
    try:
        session = get_db_session()
        session.execute("SELECT 1")
        session.close()
        logger.debug("Database connection validated successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection validation failed: {str(e)}")
        database_errors_total.labels(error_type="validation").inc()
        raise
