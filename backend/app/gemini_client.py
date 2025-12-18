"""
Google Gemini API client for generating human-readable explanations.
"""
import json
from typing import Dict, Any
import google.generativeai as genai
from .config import config


def slim_transaction(tx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce transaction data to essential fields only.
    Dramatically reduces token usage for Gemini API.
    
    Args:
        tx: Full transaction data from Sui RPC
        
    Returns:
        Slimmed transaction with only essential fields
    """
    transaction_data = tx.get("transaction", {}).get("data", {})
    effects = tx.get("effects", {})
    
    return {
        "digest": tx.get("digest"),
        "sender": transaction_data.get("sender"),
        "gas": {
            "computationCost": effects.get("gasUsed", {}).get("computationCost"),
            "storageCost": effects.get("gasUsed", {}).get("storageCost"),
            "storageRebate": effects.get("gasUsed", {}).get("storageRebate"),
        },
        "status": effects.get("status"),
        "objectChanges": tx.get("objectChanges", []),
        "balanceChanges": tx.get("balanceChanges", []),
        "transactions": transaction_data.get("transaction", {}).get("transactions", []),
        "events": tx.get("events", [])
    }


class GeminiClient:
    """Client for Google Gemini API."""
    
    SYSTEM_PROMPT = """You are an expert at analyzing Sui blockchain transactions and presenting them in a structured, easy-to-understand format.

Your task is to analyze the raw Sui RPC transaction response and return a JSON object with the following structure:

{
  "summary": "A human-readable explanation in plain English (3-5 sentences for simple transactions, more for complex ones)",
  "objects": {
    "created": [
      {
        "object_id": "full object ID",
        "object_type": "full object type string",
        "owner": "owner address or null",
        "version": "version number or null"
      }
    ],
    "mutated": [ /* same structure as created */ ],
    "deleted": [ /* same structure as created */ ]
  },
  "packages": [
    {
      "package_id": "package address",
      "module": "module name or null",
      "function": "function name or null"
    }
  ],
  "diagram": {
    "nodes": [
      {
        "id": "unique_node_id",
        "label": "display label (truncate addresses to 8...4 format)",
        "type": "address|object|package"
      }
    ],
    "edges": [
      {
        "source": "source_node_id",
        "target": "target_node_id",
        "label": "edge label (e.g., 'calls', 'created', 'modified', transfer amount)",
        "type": "transfer|mutation|creation|deletion"
      }
    ]
  }
}

Guidelines for summary:
- Use simple, everyday language - avoid jargon
- Focus on what happened: what was sent, what changed, who was involved
- Mention gas costs in user-friendly terms
- Explain what object creation/mutation means in context

Guidelines for objects:
- Extract from objectChanges array in the response
- Categorize by type: created, mutated, deleted (or wrapped)
- Include all relevant metadata

Guidelines for packages:
- Extract from transaction.data.transaction.transactions MoveCall entries
- Include package ID, module, and function names

Guidelines for diagram:
- Create nodes for: sender address, recipient addresses, packages called, objects created/modified
- Create edges showing relationships: who calls what, what creates what, what modifies what
- Use descriptive labels
- Truncate addresses to format: "0x1234...5678"

Return ONLY valid JSON, no markdown formatting or additional text.

Now analyze this transaction:
"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
    
    async def analyze_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze transaction and return structured data.
        
        Args:
            transaction_data: Raw transaction data from Sui RPC
            
        Returns:
            Dictionary with summary, objects, packages, and diagram
        """
        # Slim down transaction to essential fields (saves tokens!)
        slimmed_data = slim_transaction(transaction_data)
        
        # Format slimmed data as compact JSON (no indentation to save tokens)
        transaction_json = json.dumps(slimmed_data)
        
        # Construct prompt
        prompt = f"{self.SYSTEM_PROMPT}\n\n{transaction_json}"
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract text from response
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                response_text = response.candidates[0].content.parts[0].text.strip()
            
            if not response_text:
                raise ValueError("No response text received from Gemini")
            
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove opening ```json or ```
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.strip()
            
            # Parse JSON response
            parsed_response = json.loads(response_text)
            
            return parsed_response
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini JSON response: {e}")
            print(f"Response text: {response_text[:500] if response_text else 'None'}")
            # Raise exception instead of returning error object
            raise ValueError(f"Failed to parse Gemini response: {e}")
        except Exception as e:
            print(f"Error in Gemini analysis: {str(e)}")
            # Re-raise exception instead of returning error object
            raise


# Global Gemini client instance
gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance."""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client
