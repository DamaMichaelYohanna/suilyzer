"""
Utility functions for the Suilyzer backend.
"""
from typing import Optional, Any


def format_sui_amount(amount: int) -> str:
    """
    Format MIST amount to SUI with proper decimals.
    
    Args:
        amount: Amount in MIST (1 SUI = 1,000,000,000 MIST)
        
    Returns:
        Formatted string like "0.05 SUI"
    """
    sui_amount = amount / 1_000_000_000
    return f"{sui_amount:.9f}".rstrip('0').rstrip('.') + " SUI"


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        *keys: Nested keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at nested key path or default
    """
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def truncate_address(address: str, start_chars: int = 6, end_chars: int = 4) -> str:
    """
    Truncate blockchain address for display.
    
    Args:
        address: Full address
        start_chars: Number of characters to show at start
        end_chars: Number of characters to show at end
        
    Returns:
        Truncated address like "0x1234...5678"
    """
    if len(address) <= start_chars + end_chars + 3:
        return address
    return f"{address[:start_chars]}...{address[-end_chars:]}"


def extract_object_type(object_type: str) -> dict:
    """
    Parse a Sui object type string into components.
    
    Args:
        object_type: Full object type like "0x2::coin::Coin<0x2::sui::SUI>"
        
    Returns:
        Dictionary with package, module, struct, and type_args
    """
    result = {
        "package": None,
        "module": None,
        "struct": None,
        "type_args": None,
        "full": object_type
    }
    
    try:
        # Split on < to separate base type from type arguments
        if '<' in object_type:
            base_type, type_args = object_type.split('<', 1)
            result["type_args"] = type_args.rstrip('>')
        else:
            base_type = object_type
        
        # Split base type into package::module::struct
        parts = base_type.split('::')
        if len(parts) >= 3:
            result["package"] = parts[0]
            result["module"] = parts[1]
            result["struct"] = '::'.join(parts[2:])
        elif len(parts) == 2:
            result["module"] = parts[0]
            result["struct"] = parts[1]
        else:
            result["struct"] = base_type
    except Exception:
        pass
    
    return result


def is_sui_coin(object_type: str) -> bool:
    """
    Check if object type is a SUI coin.
    
    Args:
        object_type: Object type string
        
    Returns:
        True if this is a SUI coin
    """
    return "0x2::coin::Coin<0x2::sui::SUI>" in object_type


def format_object_id(object_id: str) -> str:
    """
    Format object ID for display (ensure 0x prefix).
    
    Args:
        object_id: Object ID
        
    Returns:
        Formatted object ID
    """
    if not object_id.startswith("0x"):
        return f"0x{object_id}"
    return object_id
