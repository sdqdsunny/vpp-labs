"""
Protocol Mapping Data Model

Represents protocol conversion mappings between different communication protocols.
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Index
from datetime import datetime
from utils.database import Base


class ProtocolMapping(Base):
    """
    Protocol mapping model for protocol conversion configuration
    
    Attributes:
        id: Unique mapping identifier (primary key)
        source_protocol: Source protocol type (iec_104, mqtt, etc.)
        target_protocol: Target protocol type
        mapping_rules: JSON object containing mapping rules
        is_active: Whether this mapping is active
        created_at: Timestamp when mapping was created
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "protocol_mappings"
    
    # Primary key
    id = Column(String(255), primary_key=True, nullable=False)
    
    # Protocol information
    source_protocol = Column(String(50), nullable=False, index=True)
    target_protocol = Column(String(50), nullable=False, index=True)
    
    # Mapping configuration
    mapping_rules = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for query optimization
    __table_args__ = (
        Index('idx_protocol_source_target', 'source_protocol', 'target_protocol'),
        Index('idx_protocol_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ProtocolMapping(id={self.id}, {self.source_protocol}->{self.target_protocol})>"
    
    def to_dict(self):
        """Convert protocol mapping to dictionary"""
        return {
            "id": self.id,
            "source_protocol": self.source_protocol,
            "target_protocol": self.target_protocol,
            "mapping_rules": self.mapping_rules,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def is_enabled(self):
        """Check if mapping is enabled"""
        return self.is_active
    
    def enable(self):
        """Enable this mapping"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def disable(self):
        """Disable this mapping"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_rules(self, new_rules: dict):
        """Update mapping rules"""
        self.mapping_rules.update(new_rules)
        self.updated_at = datetime.utcnow()
