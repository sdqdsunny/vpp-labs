"""
SQLAlchemy database models for real-time data exchange.

Defines ORM models for:
- Power generation data
- Storage data
- Demand data
- Coordination results
- Commands
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class PowerGenerationDataDB(Base):
    """Power generation data database model."""
    __tablename__ = 'power_generation_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    current_power = Column(Float, nullable=False)
    solar_power = Column(Float, nullable=False)
    wind_power = Column(Float, nullable=False)
    efficiency = Column(Float, nullable=False)
    device_status = Column(String(50), nullable=False)
    module_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_power_timestamp_module', 'timestamp', 'module_id'),
    )


class StorageDataDB(Base):
    """Storage data database model."""
    __tablename__ = 'storage_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    soc = Column(Float, nullable=False)
    soh = Column(Float, nullable=False)
    current_power = Column(Float, nullable=False)
    charge_status = Column(String(50), nullable=False)
    temperature = Column(Float, nullable=False)
    module_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_storage_timestamp_module', 'timestamp', 'module_id'),
    )


class DemandDataDB(Base):
    """Demand data database model."""
    __tablename__ = 'demand_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    current_load = Column(Float, nullable=False)
    forecast_load = Column(Float, nullable=False)
    adjustable_range_min = Column(Float, nullable=False)
    adjustable_range_max = Column(Float, nullable=False)
    dr_status = Column(String(50), nullable=False)
    module_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_demand_timestamp_module', 'timestamp', 'module_id'),
    )


class CoordinationResultDB(Base):
    """Coordination result database model."""
    __tablename__ = 'coordination_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    power_command = Column(JSON, nullable=False)
    storage_command = Column(JSON, nullable=False)
    demand_command = Column(JSON, nullable=False)
    optimization_score = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommandDB(Base):
    """Command database model."""
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True, autoincrement=True)
    command_id = Column(String(100), nullable=False, unique=True, index=True)
    command_type = Column(String(50), nullable=False)
    target_module = Column(String(100), nullable=False)
    command_data = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
