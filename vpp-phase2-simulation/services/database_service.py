"""
Database Service for data persistence.

Implements:
- DatabaseService: Manages database operations
- Save power generation data
- Save storage data
- Save demand data
- Save coordination results
- Save commands
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    CoordinationResult, PowerCommand, StorageCommand, DemandCommand
)
from models.realtime_db_models import (
    PowerGenerationDataDB, StorageDataDB, DemandDataDB,
    CoordinationResultDB, CommandDB, Base
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations and data persistence."""

    def __init__(self, db_session: Optional[Session] = None, use_memory_db: bool = False):
        """
        Initialize database service.
        
        Args:
            db_session: SQLAlchemy session for database operations
            use_memory_db: If True, use in-memory SQLite for testing
        """
        self.db_session = db_session
        self.use_memory_db = use_memory_db
        self.save_count = 0
        self.error_count = 0
        
        # Initialize in-memory database if needed
        if use_memory_db and db_session is None:
            engine = create_engine(
                'sqlite:///:memory:',
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )
            Base.metadata.create_all(engine)
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            self.db_session = Session()
        
        logger.info("Database Service initialized")

    def save_power_data(self, data: PowerGenerationData) -> bool:
        """
        Save power generation data to database.
        
        Args:
            data: PowerGenerationData to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                self.error_count += 1
                return False
            
            # Validate data
            if not data.validate():
                logger.error(f"Invalid power generation data: {data}")
                self.error_count += 1
                return False
            
            # Create database record
            db_record = PowerGenerationDataDB(
                timestamp=data.timestamp,
                current_power=data.current_power,
                solar_power=data.solar_power,
                wind_power=data.wind_power,
                efficiency=data.efficiency,
                device_status=data.device_status,
                module_id=data.module_id
            )
            
            self.db_session.add(db_record)
            self.db_session.commit()
            self.save_count += 1
            
            logger.debug(f"Power generation data saved: {data.module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving power generation data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            self.error_count += 1
            return False

    def save_storage_data(self, data: StorageData) -> bool:
        """
        Save storage data to database.
        
        Args:
            data: StorageData to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                self.error_count += 1
                return False
            
            # Validate data
            if not data.validate():
                logger.error(f"Invalid storage data: {data}")
                self.error_count += 1
                return False
            
            # Create database record
            db_record = StorageDataDB(
                timestamp=data.timestamp,
                soc=data.soc,
                soh=data.soh,
                current_power=data.current_power,
                charge_status=data.charge_status,
                temperature=data.temperature,
                module_id=data.module_id
            )
            
            self.db_session.add(db_record)
            self.db_session.commit()
            self.save_count += 1
            
            logger.debug(f"Storage data saved: {data.module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving storage data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            self.error_count += 1
            return False

    def save_demand_data(self, data: DemandData) -> bool:
        """
        Save demand data to database.
        
        Args:
            data: DemandData to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                self.error_count += 1
                return False
            
            # Validate data
            if not data.validate():
                logger.error(f"Invalid demand data: {data}")
                self.error_count += 1
                return False
            
            # Create database record
            db_record = DemandDataDB(
                timestamp=data.timestamp,
                current_load=data.current_load,
                forecast_load=data.forecast_load,
                adjustable_range_min=data.adjustable_range[0],
                adjustable_range_max=data.adjustable_range[1],
                dr_status=data.dr_status,
                module_id=data.module_id
            )
            
            self.db_session.add(db_record)
            self.db_session.commit()
            self.save_count += 1
            
            logger.debug(f"Demand data saved: {data.module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving demand data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            self.error_count += 1
            return False

    def save_coordination_result(self, result: CoordinationResult) -> bool:
        """
        Save coordination result to database.
        
        Args:
            result: CoordinationResult to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                self.error_count += 1
                return False
            
            # Create database record
            db_record = CoordinationResultDB(
                timestamp=result.timestamp,
                power_command=result.power_command.to_dict(),
                storage_command=result.storage_command.to_dict(),
                demand_command=result.demand_command.to_dict(),
                optimization_score=result.optimization_score,
                status=result.status
            )
            
            self.db_session.add(db_record)
            self.db_session.commit()
            self.save_count += 1
            
            logger.debug(f"Coordination result saved: score={result.optimization_score}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving coordination result: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            self.error_count += 1
            return False

    def save_command(self,
                    command_id: str,
                    command_type: str,
                    target_module: str,
                    command_data: dict,
                    status: str = "pending") -> bool:
        """
        Save command to database.
        
        Args:
            command_id: Command ID
            command_type: Type of command (power/storage/demand)
            target_module: Target module
            command_data: Command data
            status: Command status
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                self.error_count += 1
                return False
            
            # Create database record
            db_record = CommandDB(
                command_id=command_id,
                command_type=command_type,
                target_module=target_module,
                command_data=command_data,
                status=status
            )
            
            self.db_session.add(db_record)
            self.db_session.commit()
            self.save_count += 1
            
            logger.debug(f"Command saved: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving command: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            self.error_count += 1
            return False

    def update_command_status(self,
                             command_id: str,
                             status: str,
                             result: Optional[dict] = None) -> bool:
        """
        Update command status in database.
        
        Args:
            command_id: Command ID
            status: New status
            result: Execution result
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                return False
            
            # Query command
            command = self.db_session.query(CommandDB).filter_by(
                command_id=command_id
            ).first()
            
            if not command:
                logger.warning(f"Command not found: {command_id}")
                return False
            
            # Update command
            command.status = status
            command.result = result
            command.executed_at = datetime.now()
            
            self.db_session.commit()
            
            logger.debug(f"Command status updated: {command_id}, status={status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating command status: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False

    def query_power_data(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[PowerGenerationDataDB]:
        """
        Query power generation data from database.
        
        Args:
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records to return
            
        Returns:
            List of PowerGenerationDataDB records
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                return []
            
            query = self.db_session.query(PowerGenerationDataDB)
            
            if start_time:
                query = query.filter(PowerGenerationDataDB.timestamp >= start_time)
            if end_time:
                query = query.filter(PowerGenerationDataDB.timestamp <= end_time)
            
            records = query.order_by(PowerGenerationDataDB.timestamp.desc()).limit(limit).all()
            
            logger.debug(f"Queried {len(records)} power generation records")
            return records
            
        except Exception as e:
            logger.error(f"Error querying power data: {str(e)}")
            return []

    def query_storage_data(self,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          limit: int = 100) -> List[StorageDataDB]:
        """
        Query storage data from database.
        
        Args:
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records to return
            
        Returns:
            List of StorageDataDB records
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                return []
            
            query = self.db_session.query(StorageDataDB)
            
            if start_time:
                query = query.filter(StorageDataDB.timestamp >= start_time)
            if end_time:
                query = query.filter(StorageDataDB.timestamp <= end_time)
            
            records = query.order_by(StorageDataDB.timestamp.desc()).limit(limit).all()
            
            logger.debug(f"Queried {len(records)} storage records")
            return records
            
        except Exception as e:
            logger.error(f"Error querying storage data: {str(e)}")
            return []

    def query_demand_data(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[DemandDataDB]:
        """
        Query demand data from database.
        
        Args:
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records to return
            
        Returns:
            List of DemandDataDB records
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                return []
            
            query = self.db_session.query(DemandDataDB)
            
            if start_time:
                query = query.filter(DemandDataDB.timestamp >= start_time)
            if end_time:
                query = query.filter(DemandDataDB.timestamp <= end_time)
            
            records = query.order_by(DemandDataDB.timestamp.desc()).limit(limit).all()
            
            logger.debug(f"Queried {len(records)} demand records")
            return records
            
        except Exception as e:
            logger.error(f"Error querying demand data: {str(e)}")
            return []

    def query_coordination_results(self,
                                  start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None,
                                  limit: int = 100) -> List[CoordinationResultDB]:
        """
        Query coordination results from database.
        
        Args:
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of records to return
            
        Returns:
            List of CoordinationResultDB records
        """
        try:
            if not self.db_session:
                logger.error("Database session not available")
                return []
            
            query = self.db_session.query(CoordinationResultDB)
            
            if start_time:
                query = query.filter(CoordinationResultDB.timestamp >= start_time)
            if end_time:
                query = query.filter(CoordinationResultDB.timestamp <= end_time)
            
            records = query.order_by(CoordinationResultDB.timestamp.desc()).limit(limit).all()
            
            logger.debug(f"Queried {len(records)} coordination results")
            return records
            
        except Exception as e:
            logger.error(f"Error querying coordination results: {str(e)}")
            return []

    def get_stats(self) -> dict:
        """
        Get database service statistics.
        
        Returns:
            dict: Statistics including save count and error count
        """
        return {
            "save_count": self.save_count,
            "error_count": self.error_count,
            "has_session": self.db_session is not None,
        }

    def close(self):
        """Close database session."""
        if self.db_session:
            self.db_session.close()
            logger.info("Database session closed")
