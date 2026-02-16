"""
Database Transaction Management

Provides transaction wrappers, rollback mechanisms, and connection pooling utilities
for reliable data persistence and consistency.
"""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import setup_logger
from utils.metrics import database_errors_total

logger = setup_logger(__name__)

T = TypeVar('T')


class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass


class TransactionRollbackError(TransactionError):
    """Exception raised when transaction rollback fails"""
    pass


class TransactionCommitError(TransactionError):
    """Exception raised when transaction commit fails"""
    pass


@contextmanager
def transaction(session: Session, name: str = "transaction"):
    """
    Context manager for database transactions with automatic rollback on failure.
    
    Ensures that:
    - All operations within the context are part of a single transaction
    - Changes are committed if no exception occurs
    - All changes are rolled back if an exception occurs
    - Connection is properly returned to the pool
    
    Args:
        session: SQLAlchemy session instance
        name: Optional name for logging purposes
        
    Yields:
        The session instance for use within the context
        
    Raises:
        TransactionRollbackError: If rollback fails
        TransactionCommitError: If commit fails
        
    Example:
        with transaction(session, "register_device") as tx_session:
            device = Device(id="dev-1", device_type="solar")
            tx_session.add(device)
            # Automatically commits on success, rolls back on exception
    """
    try:
        logger.debug(f"Starting transaction: {name}")
        yield session
        
        # Commit the transaction
        try:
            session.commit()
            logger.debug(f"Transaction committed: {name}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit transaction {name}: {str(e)}")
            database_errors_total.labels(error_type="commit").inc()
            raise TransactionCommitError(f"Failed to commit transaction {name}: {str(e)}") from e
            
    except TransactionCommitError:
        # Re-raise commit errors without attempting rollback
        raise
    except Exception as e:
        # Rollback on any other exception
        try:
            logger.warning(f"Rolling back transaction {name} due to error: {str(e)}")
            session.rollback()
            logger.debug(f"Transaction rolled back: {name}")
            database_errors_total.labels(error_type="rollback").inc()
        except SQLAlchemyError as rollback_error:
            logger.error(f"Failed to rollback transaction {name}: {str(rollback_error)}")
            database_errors_total.labels(error_type="rollback_failure").inc()
            raise TransactionRollbackError(
                f"Failed to rollback transaction {name}: {str(rollback_error)}"
            ) from rollback_error
        
        # Re-raise the original exception
        raise
    finally:
        # Ensure session is closed/returned to pool
        try:
            session.close()
            logger.debug(f"Session closed for transaction: {name}")
        except Exception as e:
            logger.error(f"Error closing session for transaction {name}: {str(e)}")


def transactional(name: Optional[str] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for automatic transaction management on service methods.
    
    Wraps a method to automatically manage database transactions:
    - Commits on successful completion
    - Rolls back on exception
    - Properly closes the session
    
    Args:
        name: Optional transaction name for logging. If not provided, uses function name.
        
    Returns:
        Decorated function that manages transactions automatically
        
    Example:
        @transactional("register_device")
        def register_device(self, session: Session, device_data: dict) -> Device:
            device = Device(**device_data)
            session.add(device)
            return device
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Extract session from kwargs or args
            session = kwargs.get('session')
            if session is None and len(args) > 1:
                # Assume second argument is session (after self)
                session = args[1]
            
            if session is None:
                raise ValueError(f"No session provided to transactional function {func.__name__}")
            
            tx_name = name or func.__name__
            with transaction(session, tx_name):
                return func(*args, **kwargs)
        
        return cast(Callable[..., T], wrapper)
    
    return decorator


def ensure_committed(session: Session, obj: Any) -> Any:
    """
    Ensure an object is committed to the database and refresh it.
    
    This is useful after operations to ensure the object reflects
    the current database state, including any database-generated values.
    
    Args:
        session: SQLAlchemy session instance
        obj: The object to refresh
        
    Returns:
        The refreshed object
        
    Raises:
        TransactionError: If refresh fails
    """
    try:
        session.refresh(obj)
        logger.debug(f"Object refreshed from database: {type(obj).__name__}")
        return obj
    except SQLAlchemyError as e:
        logger.error(f"Failed to refresh object: {str(e)}")
        database_errors_total.labels(error_type="refresh").inc()
        raise TransactionError(f"Failed to refresh object: {str(e)}") from e


def get_connection_pool_status(engine: Any) -> dict:
    """
    Get the current status of the database connection pool.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Dictionary with pool status information
    """
    pool = engine.pool
    
    status = {
        "pool_class": pool.__class__.__name__,
        "pool_size": getattr(pool, 'pool_size', None),
        "max_overflow": getattr(pool, 'max_overflow', None),
        "checked_out": getattr(pool, 'checkedout', lambda: None)(),
        "checked_in": getattr(pool, 'checkedin', lambda: None)(),
    }
    
    logger.debug(f"Connection pool status: {status}")
    return status


def validate_transaction_state(session: Session) -> bool:
    """
    Validate that a session is in a valid transaction state.
    
    Args:
        session: SQLAlchemy session instance
        
    Returns:
        True if session is valid, False otherwise
    """
    try:
        # Check if session is active
        if not session.is_active:
            logger.warning("Session is not active")
            return False
        
        # Check if there's an active transaction
        if session.in_transaction():
            logger.debug("Session has active transaction")
        
        return True
    except Exception as e:
        logger.error(f"Error validating transaction state: {str(e)}")
        return False
