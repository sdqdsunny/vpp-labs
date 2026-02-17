"""
Protocol Message Mapper

Handles mapping and transformation of messages between different protocols.
"""

from typing import Dict, Any, Callable, Optional, List
from .base import ProtocolMessage, MessageException
import logging

logger = logging.getLogger(__name__)


class ProtocolMessageMapper:
    """
    Maps and transforms messages between different protocols.
    
    Supports:
    - Direct field mapping
    - Conditional mapping
    - Custom transformers
    - Message validation
    """

    def __init__(self):
        """Initialize mapper"""
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self.transformers: Dict[str, Callable] = {}
        self.validators: Dict[str, Callable] = {}

    def register_mapping(
        self,
        source_protocol: str,
        target_protocol: str,
        mapping_rules: Dict[str, Any],
    ) -> None:
        """
        Register mapping rules between protocols.
        
        Args:
            source_protocol: Source protocol name
            target_protocol: Target protocol name
            mapping_rules: Mapping rules dictionary
            
        Example:
            mapper.register_mapping(
                "iec61850",
                "modbus",
                {
                    "voltage": "holding_register_0",
                    "current": {"source": "holding_register_1", "transformer": "scale_current"},
                }
            )
        """
        key = f"{source_protocol}->{target_protocol}"
        self.mappings[key] = mapping_rules
        logger.info(f"Registered mapping: {key}")

    def register_transformer(
        self,
        name: str,
        transformer: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Register custom data transformer.
        
        Args:
            name: Transformer name
            transformer: Callable that transforms data
        """
        self.transformers[name] = transformer
        logger.info(f"Registered transformer: {name}")

    def register_validator(
        self,
        name: str,
        validator: Callable[[Dict[str, Any]], bool],
    ) -> None:
        """
        Register custom message validator.
        
        Args:
            name: Validator name
            validator: Callable that validates message
        """
        self.validators[name] = validator
        logger.info(f"Registered validator: {name}")

    def map_message(
        self,
        source_protocol: str,
        target_protocol: str,
        message: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map message from source protocol to target protocol.
        
        Args:
            source_protocol: Source protocol name
            target_protocol: Target protocol name
            message: Message to map
            
        Returns:
            Mapped message
            
        Raises:
            MessageException: If mapping fails
        """
        key = f"{source_protocol}->{target_protocol}"

        if key not in self.mappings:
            raise MessageException(f"No mapping found: {key}")

        try:
            mapping_rules = self.mappings[key]
            return self._apply_mapping(message, mapping_rules)
        except Exception as e:
            logger.error(f"Mapping failed: {e}")
            raise MessageException(f"Failed to map message: {e}")

    def transform_data(
        self,
        transformer_name: str,
        data: Dict[str, Any],
    ) -> Any:
        """
        Apply custom transformer to data.
        
        Args:
            transformer_name: Name of transformer
            data: Data to transform
            
        Returns:
            Transformed data
            
        Raises:
            MessageException: If transformer not found
        """
        if transformer_name not in self.transformers:
            raise MessageException(f"Unknown transformer: {transformer_name}")

        try:
            return self.transformers[transformer_name](data)
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            raise MessageException(f"Failed to transform data: {e}")

    def validate_message(
        self,
        validator_name: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        Validate message using custom validator.
        
        Args:
            validator_name: Name of validator
            message: Message to validate
            
        Returns:
            True if valid, False otherwise
        """
        if validator_name not in self.validators:
            logger.warning(f"Unknown validator: {validator_name}")
            return True

        try:
            return self.validators[validator_name](message)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def _apply_mapping(
        self,
        message: Dict[str, Any],
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply mapping rules to message.
        
        Args:
            message: Source message
            rules: Mapping rules
            
        Returns:
            Mapped message
        """
        result = {}

        for target_field, rule in rules.items():
            try:
                if isinstance(rule, str):
                    # Direct field mapping
                    result[target_field] = message.get(rule)

                elif isinstance(rule, dict):
                    # Complex mapping
                    if "transformer" in rule:
                        # Apply transformer
                        transformer = self.transformers[rule["transformer"]]
                        result[target_field] = transformer(message)

                    elif "source" in rule:
                        # Source field mapping
                        result[target_field] = message.get(rule["source"])

                    elif "default" in rule:
                        # Default value
                        result[target_field] = rule["default"]

                    elif "condition" in rule:
                        # Conditional mapping
                        condition = rule["condition"]
                        if self._evaluate_condition(message, condition):
                            result[target_field] = rule.get("value")

                else:
                    # Direct value
                    result[target_field] = rule

            except Exception as e:
                logger.warning(f"Failed to map field {target_field}: {e}")
                result[target_field] = None

        return result

    def _evaluate_condition(
        self,
        message: Dict[str, Any],
        condition: Dict[str, Any],
    ) -> bool:
        """
        Evaluate conditional mapping.
        
        Args:
            message: Message to evaluate
            condition: Condition dictionary
            
        Returns:
            True if condition is met
        """
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field not in message:
            return False

        msg_value = message[field]

        if operator == "eq":
            return msg_value == value
        elif operator == "ne":
            return msg_value != value
        elif operator == "gt":
            return msg_value > value
        elif operator == "lt":
            return msg_value < value
        elif operator == "gte":
            return msg_value >= value
        elif operator == "lte":
            return msg_value <= value
        elif operator == "in":
            return msg_value in value
        elif operator == "not_in":
            return msg_value not in value

        return False

    def get_mapping_info(self) -> Dict[str, Any]:
        """
        Get mapper information.
        
        Returns:
            Mapper info dictionary
        """
        return {
            "mappings": list(self.mappings.keys()),
            "transformers": list(self.transformers.keys()),
            "validators": list(self.validators.keys()),
            "total_mappings": len(self.mappings),
            "total_transformers": len(self.transformers),
            "total_validators": len(self.validators),
        }
