"""
Sui RPC client for fetching transaction data.
"""
import httpx
from typing import Dict, Any, Optional
from .config import config


class SuiRPCClient:
    """Client for interacting with Sui RPC endpoint."""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Sui RPC client.
        
        Args:
            rpc_url: Sui RPC endpoint URL
        """
        self.rpc_url = rpc_url or config.SUI_RPC_URL
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry - create client."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, ensuring it exists."""
        if self._client is None:
            raise RuntimeError("SuiRPCClient must be used as async context manager")
        return self._client
    
    async def _rpc_call(self, method: str, params: list) -> Dict[str, Any]:
        """
        Make an RPC call to Sui node.
        
        Args:
            method: RPC method name
            params: Method parameters
            
        Returns:
            RPC response result
            
        Raises:
            Exception: If RPC call fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        response = await self.client.post(self.rpc_url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown RPC error")
            raise Exception(f"Sui RPC error: {error_msg}")
        
        if "result" not in data:
            raise Exception("Invalid RPC response: missing result field")
        
        return data["result"]
    
    async def get_transaction_block(self, digest: str) -> Dict[str, Any]:
        """
        Fetch transaction block with full details.
        
        Args:
            digest: Transaction digest
            
        Returns:
            Transaction data including effects, object changes, balance changes, and events
            
        Raises:
            Exception: If transaction not found or RPC call fails
        """
        params = [
            digest,
            {
                "showInput": True,
                "showRawInput": False,
                "showEffects": True,
                "showEvents": True,
                "showObjectChanges": True,
                "showBalanceChanges": True
            }
        ]
        
        return await self._rpc_call("sui_getTransactionBlock", params)
    
    async def get_object(self, object_id: str) -> Dict[str, Any]:
        """
        Fetch object details.
        
        Args:
            object_id: Object ID
            
        Returns:
            Object data
        """
        params = [
            object_id,
            {
                "showType": True,
                "showOwner": True,
                "showPreviousTransaction": True,
                "showStorageRebate": True,
                "showContent": True
            }
        ]
        
        return await self._rpc_call("sui_getObject", params)


def get_sui_rpc_client() -> SuiRPCClient:
    """Factory function to create new RPC client instance."""
    return SuiRPCClient()
