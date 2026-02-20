"""
Component Information Data Model

Represents information about a VPP system component.
"""

from dataclasses import dataclass
from typing import Tuple, Literal


@dataclass
class ComponentInfo:
    """
    Represents VPP system component information
    
    Attributes:
        name: Component name
        ip_address: IP address of the component
        component_type: Type of component ('coordinator', 'power', 'storage', 'demand')
        position: 3D position coordinates (x, y, z)
        status: Component status ('online' or 'offline')
        color: Component color in hex format
    """
    
    name: str
    ip_address: str
    component_type: Literal['coordinator', 'power', 'storage', 'demand']
    position: Tuple[float, float, float]
    status: Literal['online', 'offline']
    color: str
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.component_type not in ('coordinator', 'power', 'storage', 'demand'):
            raise ValueError(f"Invalid component type: {self.component_type}")
        
        if self.status not in ('online', 'offline'):
            raise ValueError(f"Invalid status: {self.status}")
        
        if not self._is_valid_hex_color(self.color):
            raise ValueError(f"Invalid hex color: {self.color}")
    
    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """Check if color is valid hex format"""
        if not color.startswith('#'):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            'name': self.name,
            'ip': self.ip_address,
            'type': self.component_type,
            'position': self.position,
            'status': self.status,
            'color': self.color
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComponentInfo':
        """Create from dictionary format"""
        return cls(
            name=data['name'],
            ip_address=data['ip'],
            component_type=data['type'],
            position=tuple(data['position']),
            status=data['status'],
            color=data['color']
        )
    
    def __repr__(self) -> str:
        return (f"ComponentInfo(name={self.name}, ip={self.ip_address}, "
                f"type={self.component_type}, status={self.status})")
