"""
Parser for Sui transaction data.
"""
from typing import Dict, Any, List, Optional
from .utils import safe_get, format_sui_amount, extract_object_type
from .schemas import ObjectChange, ObjectChanges, PackageInfo


class TransactionParser:
    """Parser for Sui transaction data."""
    
    def __init__(self, transaction_data: Dict[str, Any]):
        """
        Initialize parser with transaction data.
        
        Args:
            transaction_data: Raw transaction data from Sui RPC
        """
        self.data = transaction_data
        self.effects = safe_get(transaction_data, "effects", default={})
        self.object_changes = safe_get(transaction_data, "objectChanges", default=[])
        self.balance_changes = safe_get(transaction_data, "balanceChanges", default=[])
        self.events = safe_get(transaction_data, "events", default=[])
        self.transaction = safe_get(transaction_data, "transaction", default={})
    
    def get_gas_used(self) -> str:
        """
        Extract and format gas used.
        
        Returns:
            Formatted gas string like "0.005 SUI"
        """
        gas_used = safe_get(
            self.effects, 
            "gasUsed", 
            "computationCost", 
            default=0
        )
        
        if not gas_used:
            # Try alternative path
            gas_object = safe_get(self.effects, "gasUsed", default={})
            if isinstance(gas_object, dict):
                computation_cost = int(gas_object.get("computationCost", 0))
                storage_cost = int(gas_object.get("storageCost", 0))
                storage_rebate = int(gas_object.get("storageRebate", 0))
                gas_used = computation_cost + storage_cost - storage_rebate
        
        return format_sui_amount(int(gas_used))
    
    def get_object_changes(self) -> ObjectChanges:
        """
        Parse object changes (created, mutated, deleted).
        
        Returns:
            ObjectChanges with categorized object changes
        """
        created = []
        mutated = []
        deleted = []
        
        for change in self.object_changes:
            change_type = change.get("type")
            
            if change_type == "created":
                created.append(self._parse_object_change(change))
            elif change_type == "mutated":
                mutated.append(self._parse_object_change(change))
            elif change_type == "deleted":
                deleted.append(self._parse_object_change(change))
            elif change_type == "wrapped":
                # Wrapped objects are similar to deleted
                deleted.append(self._parse_object_change(change))
            elif change_type == "published":
                # Published packages as created
                created.append(self._parse_object_change(change))
        
        return ObjectChanges(created=created, mutated=mutated, deleted=deleted)
    
    def _parse_object_change(self, change: Dict[str, Any]) -> ObjectChange:
        """
        Parse a single object change.
        
        Args:
            change: Object change data
            
        Returns:
            ObjectChange instance
        """
        object_id = change.get("objectId", "unknown")
        object_type = change.get("objectType", "unknown")
        
        owner = None
        if "owner" in change:
            owner_data = change["owner"]
            if isinstance(owner_data, dict):
                if "AddressOwner" in owner_data:
                    owner = owner_data["AddressOwner"]
                elif "ObjectOwner" in owner_data:
                    owner = f"Object({owner_data['ObjectOwner']})"
                elif "Shared" in owner_data:
                    owner = "Shared"
            elif isinstance(owner_data, str):
                owner = owner_data
        
        digest = change.get("digest")
        version = change.get("version")
        
        return ObjectChange(
            object_id=object_id,
            object_type=object_type,
            owner=owner,
            digest=digest,
            version=str(version) if version else None
        )
    
    def get_packages(self) -> List[PackageInfo]:
        """
        Extract packages and modules involved in transaction.
        
        Returns:
            List of PackageInfo
        """
        packages = []
        
        # Get from transaction data
        tx_data = safe_get(self.transaction, "data", default={})
        
        # Check for move call
        if "transaction" in tx_data:
            tx_kind = tx_data["transaction"]
            
            if isinstance(tx_kind, dict) and "MoveCall" in tx_kind:
                move_call = tx_kind["MoveCall"]
                package_id = move_call.get("package")
                module = move_call.get("module")
                function = move_call.get("function")
                
                if package_id:
                    packages.append(PackageInfo(
                        package_id=package_id,
                        module=module,
                        function=function
                    ))
        
        # Also check published packages
        for change in self.object_changes:
            if change.get("type") == "published":
                package_id = change.get("packageId", change.get("objectId"))
                if package_id:
                    packages.append(PackageInfo(
                        package_id=package_id,
                        module=None,
                        function=None
                    ))
        
        return packages
    
    def get_sender(self) -> Optional[str]:
        """
        Get transaction sender address.
        
        Returns:
            Sender address or None
        """
        return safe_get(self.transaction, "data", "sender")
    
    def get_recipients(self) -> List[str]:
        """
        Get recipient addresses from balance changes.
        
        Returns:
            List of recipient addresses
        """
        recipients = set()
        
        for balance_change in self.balance_changes:
            owner = balance_change.get("owner")
            if isinstance(owner, dict) and "AddressOwner" in owner:
                recipients.add(owner["AddressOwner"])
        
        return list(recipients)
    
    def get_coin_transfers(self) -> List[Dict[str, Any]]:
        """
        Extract coin transfer information.
        
        Returns:
            List of transfer dictionaries
        """
        transfers = []
        
        for balance_change in self.balance_changes:
            amount = balance_change.get("amount")
            coin_type = balance_change.get("coinType", "0x2::sui::SUI")
            
            owner = None
            owner_data = balance_change.get("owner", {})
            if isinstance(owner_data, dict) and "AddressOwner" in owner_data:
                owner = owner_data["AddressOwner"]
            
            if owner and amount:
                transfers.append({
                    "address": owner,
                    "amount": amount,
                    "coin_type": coin_type,
                    "formatted_amount": format_sui_amount(abs(int(amount)))
                })
        
        return transfers
    
    def to_structured_data(self) -> Dict[str, Any]:
        """
        Convert transaction to structured data for Gemini.
        
        Returns:
            Dictionary with all parsed transaction data
        """
        return {
            "sender": self.get_sender(),
            "recipients": self.get_recipients(),
            "gas_used": self.get_gas_used(),
            "object_changes": {
                "created": [obj.model_dump() for obj in self.get_object_changes().created],
                "mutated": [obj.model_dump() for obj in self.get_object_changes().mutated],
                "deleted": [obj.model_dump() for obj in self.get_object_changes().deleted],
            },
            "packages": [pkg.model_dump() for pkg in self.get_packages()],
            "coin_transfers": self.get_coin_transfers(),
            "events_count": len(self.events),
        }
