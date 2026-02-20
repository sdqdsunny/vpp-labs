"""
VCC Master data reception service implementation.

Handles receiving and storing data from all side modules:
- Power generation data
- Storage data
- Demand data

Features:
- Data validation
- Database persistence
- Cache updates
- Error handling and logging
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData
)
from models.realtime_db_models import (
    PowerGenerationDataDB, StorageDataDB, DemandDataDB, Base
)
from services.realtime_data_service import DataReceptionService

logger = logging.getLogger(__name__)


class VCCDataReceptionService(DataReceptionService):
    """VCC Master data reception service implementation."""

    def __init__(self, db_session: Optional[Session] = None, use_memory_db: bool = False):
        """
        Initialize the data reception service.
        
        Args:
            db_session: SQLAlchemy session for database operations
            use_memory_db: If True, use in-memory SQLite for testing
        """
        self.db_session = db_session
        self.use_memory_db = use_memory_db
        self.cache = {}  # Simple in-memory cache for latest data
        
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
        
        logger.info("VCC Data Reception Service initialized")

    def receive_power_generation_data(self, data: PowerGenerationData) -> bool:
        """
        Receive and store power generation data.
        
        Args:
            data: Power generation data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        try:
            # Validate data
            if not data.validate():
                logger.error(f"Invalid power generation data: {data}")
                return False
            
            # Store to database if session available
            if self.db_session:
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
                logger.debug(f"Power generation data stored: {data.module_id}")
            
            # Update cache
            self.cache['power_generation'] = data
            logger.info(f"Power generation data received from {data.module_id}: "
                       f"power={data.current_power}kW, efficiency={data.efficiency}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Error receiving power generation data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False

    def receive_storage_data(self, data: StorageData) -> bool:
        """
        Receive and store storage data.
        
        Args:
            data: Storage data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        try:
            # Validate data
            if not data.validate():
                logger.error(f"Invalid storage data: {data}")
                return False
            
            # Store to database if session available
            if self.db_session:
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
                logger.debug(f"Storage data stored: {data.module_id}")
            
            # Update cache
            self.cache['storage'] = data
            logger.info(f"Storage data received from {data.module_id}: "
                       f"SOC={data.soc}%, SOH={data.soh}%, temp={data.temperature}°C")
            
            return True
            
        except Exception as e:
            logger.error(f"Error receiving storage data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False

    def receive_demand_data(self, data: DemandData) -> bool:
        """
        Receive and store demand data.
        
        Args:
            data: Demand data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        try:
            # Validate data
            if not data.validate():
                logger.error(f"Invalid demand data: {data}")
                return False
            
            # Store to database if session available
            if self.db_session:
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
                logger.debug(f"Demand data stored: {data.module_id}")
            
            # Update cache
            self.cache['demand'] = data
            logger.info(f"Demand data received from {data.module_id}: "
                       f"load={data.current_load}kW, forecast={data.forecast_load}kW")
            
            return True
            
        except Exception as e:
            logger.error(f"Error receiving demand data: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False

    def get_latest_power_data(self) -> Optional[PowerGenerationData]:
        """Get latest power generation data from cache."""
        return self.cache.get('power_generation')

    def get_latest_storage_data(self) -> Optional[StorageData]:
        """Get latest storage data from cache."""
        return self.cache.get('storage')

    def get_latest_demand_data(self) -> Optional[DemandData]:
        """Get latest demand data from cache."""
        return self.cache.get('demand')

    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        logger.debug("Cache cleared")

    def close(self):
        """Close database session."""
        if self.db_session:
            self.db_session.close()
            logger.info("Database session closed")
