"""
User and Role Models for Authentication and Authorization

Defines user accounts, roles, and permissions for the VPP Master API.
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """User account model"""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False
    
    def get_permissions(self) -> set:
        """Get all permissions for the user"""
        permissions = set()
        for role in self.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        return permissions


class Role(Base):
    """Role model for RBAC"""
    
    __tablename__ = "roles"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )


class Permission(Base):
    """Permission model for RBAC"""
    
    __tablename__ = "permissions"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    resource = Column(String, nullable=False)  # e.g., 'device', 'dispatch', 'analysis'
    action = Column(String, nullable=False)  # e.g., 'read', 'write', 'delete'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )


class AuditLog(Base):
    """Audit log for tracking operations"""
    
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)  # e.g., 'create_device', 'execute_dispatch'
    resource_type = Column(String, nullable=False)  # e.g., 'device', 'dispatch'
    resource_id = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'success', 'failure'
    details = Column(JSON, nullable=True)
    request_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.resource_type}/{self.resource_id}>"
