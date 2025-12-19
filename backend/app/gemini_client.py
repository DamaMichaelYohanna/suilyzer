"""
Google Gemini API client for generating human-readable explanations.
"""
import json
from typing import Dict, Any
import google.generativeai as genai
from .config import config


from typing import Dict, Any


from typing import Dict, Any


def slim_transaction(tx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce Sui transaction data to essential semantic fields only.
    Preserves object lifecycle information required for analysis.
    """

    transaction_data = tx.get("transaction", {}).get("data", {})
    effects = tx.get("effects", {})

    return {
        # Core identifiers
        "digest": tx.get("digest"),
        "sender": transaction_data.get("sender"),

        # Move calls
        "transactions": (
            transaction_data
            .get("transaction", {})
            .get("transactions", [])
        ),

        # ✅ CRITICAL: object lifecycle data
        "effects": {
            "created": effects.get("created", []),
            "mutated": effects.get("mutated", []),
            "deleted": effects.get("deleted", []),
        },

        # Gas (summarized)
        "gas": {
            "computationCost": effects.get("gasUsed", {}).get("computationCost"),
            "storageCost": effects.get("gasUsed", {}).get("storageCost"),
            "storageRebate": effects.get("gasUsed", {}).get("storageRebate"),
        },

        # Execution status
        "status": effects.get("status"),
    }




class GeminiClient:
    """Client for Google Gemini API."""
    
    SYSTEM_PROMPT = """Your task is to analyze the raw Sui RPC transaction response and return a JSON object with the following structure:
{
  "summary": "A human-readable explanation in plain English (3-5 sentences max) describing what the transaction does.",
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

Return ONLY valid JSON, no markdown formatting or additional text.
Use short symbolic IDs for addresses and object IDs (e.g., ADDR_1, OBJ_1).
Do not repeat full hex addresses unless necessary.
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
        print("Full transaction", transaction_data)
        slimmed_data = slim_transaction(transaction_data)
        
        # Format slimmed data as compact JSON (no indentation to save tokens)
        transaction_json = json.dumps(slimmed_data)
        print("slimmed:", transaction_json)
        
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
            print("Gemini analysis successful.", parsed_response)
            
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
