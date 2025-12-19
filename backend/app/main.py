"""
Suilyzer - Sui Transaction Analyzer
Main FastAPI application.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from .config import config
from .cache import transaction_cache
from .sui_rpc import get_sui_rpc_client
from .parser import TransactionParser
from .gemini_client import get_gemini_client
from .diagram import generate_diagram
from .schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse


# Initialize FastAPI app
app = FastAPI(
    title="Suilyzer",
    description="Analyze Sui blockchain transactions in plain English",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate configuration at module load time (fails fast)
try:
    config.validate()
    print(f"✓ Suilyzer configuration validated")
    print(f"✓ Using Sui RPC: {config.SUI_RPC_URL}")
    print(f"✓ Using Gemini model: {config.GEMINI_MODEL}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
    raise


@app.get("/")
async def root():
    """Root endpoint - redirect to app or show API info."""
    from fastapi.responses import RedirectResponse
    # Check if frontend exists, redirect to /app, otherwise show API info
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if (frontend_path / "index.html").exists():
        return RedirectResponse(url="/app")
    return {
        "name": "Suilyzer",
        "version": "1.0.0",
        "description": "Analyze Sui blockchain transactions in plain English",
        "endpoints": {
            "app": "GET /app - Frontend UI",
            "analyze": "POST /analyze - Analyze a transaction",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cache_size": transaction_cache.size(),
        "sui_rpc": config.SUI_RPC_URL
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_transaction(request: AnalyzeRequest):
    """
    Analyze a Sui transaction and return human-readable explanation.
    
    Args:
        request: AnalyzeRequest with transaction digest
        
    Returns:
        AnalyzeResponse with summary, diagram, objects, and packages
        
    Raises:
        HTTPException: If transaction not found or analysis fails
    """
    digest = request.digest.strip()
    network = request.network.lower()
    
    if not digest:
        raise HTTPException(status_code=400, detail="Transaction digest is required")
    
    # Validate network
    if network not in ['testnet', 'mainnet']:
        raise HTTPException(status_code=400, detail="Network must be 'testnet' or 'mainnet'")
    
    # Cache key includes network to avoid mixing results
    cache_key = f"{network}:{digest}"
    
    # Check cache first
    cached_result = transaction_cache.get(cache_key)
    if cached_result:
        print(f"✓ Cache hit for {network} transaction {digest[:8]}...")
        return cached_result
    
    # Get RPC URL for selected network
    rpc_url = f"https://fullnode.{network}.sui.io:443"
    
    try:
        # Fetch transaction from Sui RPC using context manager
        print(f"→ Fetching {network} transaction {digest[:8]}...")
        async with get_sui_rpc_client() as sui_client:
            sui_client.rpc_url = rpc_url  # Override RPC URL for this request
            transaction_data = await sui_client.get_transaction_block(digest)
        
        # Parse transaction with Gemini (handles everything)
        print(f"→ Analyzing transaction with Gemini AI...")
        gemini = get_gemini_client()
        gemini_analysis = await gemini.analyze_transaction(transaction_data)
        
        # Calculate gas used from raw data
        parser = TransactionParser(transaction_data)
        gas_used = parser.get_gas_used()
        
        # Convert Gemini's analysis to our response format
        from .schemas import DiagramData, ObjectChanges, ObjectChange, PackageInfo
        
        # Build diagram
        diagram = DiagramData(
            nodes=[node for node in gemini_analysis.get("diagram", {}).get("nodes", [])],
            edges=[edge for edge in gemini_analysis.get("diagram", {}).get("edges", [])]
        )
        
        # Build objects with safe conversion
        objects_data = gemini_analysis.get("objects", {})
        print(f"DEBUG: Gemini objects data: {objects_data}")
        
        try:
            created_objects = []
            for obj in objects_data.get("created", []):
                print(f"DEBUG: Processing created object: {obj}")
                # Ensure object_type is not None
                if "object_type" not in obj or obj["object_type"] is None:
                    obj["object_type"] = "unknown"
                created_objects.append(ObjectChange(**obj))
            
            mutated_objects = []
            for obj in objects_data.get("mutated", []):
                print(f"DEBUG: Processing mutated object: {obj}")
                if "object_type" not in obj or obj["object_type"] is None:
                    obj["object_type"] = "unknown"
                mutated_objects.append(ObjectChange(**obj))
            
            deleted_objects = []
            for obj in objects_data.get("deleted", []):
                print(f"DEBUG: Processing deleted object: {obj}")
                if "object_type" not in obj or obj["object_type"] is None:
                    obj["object_type"] = "unknown"
                deleted_objects.append(ObjectChange(**obj))
            
            objects = ObjectChanges(
                created=created_objects,
                mutated=mutated_objects,
                deleted=deleted_objects
            )
            print(f"DEBUG: Final objects count - Created: {len(created_objects)}, Mutated: {len(mutated_objects)}, Deleted: {len(deleted_objects)}")
        except Exception as e:
            print(f"Error parsing objects from Gemini: {e}")
            print(f"Objects data: {objects_data}")
            objects = ObjectChanges(created=[], mutated=[], deleted=[])
        
        # Build packages
        try:
            packages = [PackageInfo(**pkg) for pkg in gemini_analysis.get("packages", [])]
        except Exception as e:
            print(f"Error parsing packages from Gemini: {e}")
            packages = []
        
        # Build response
        response = AnalyzeResponse(
            summary=gemini_analysis.get("summary", "No summary available"),
            diagram=diagram,
            objects=objects,
            packages=packages,
            gas_used=gas_used,
            raw_data=transaction_data
        )
        
        # Cache ONLY successful results (not errors) - use network-specific cache key
        transaction_cache.set(cache_key, response)
        print(f"✓ {network.capitalize()} transaction {digest[:8]}... analyzed and cached")
        
        return response
    
    except HTTPException:
        # Don't cache HTTP exceptions - re-raise immediately
        raise
    except Exception as e:
        error_message = str(e)
        print(f"✗ Error analyzing transaction: {error_message}")
        
        # Don't cache errors - check for specific error types and raise appropriate HTTPException
        if "not found" in error_message.lower() or "does not exist" in error_message.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Transaction not found: {digest}"
            )
        elif "invalid" in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transaction digest: {digest}"
            )
        elif "429" in error_message or "quota" in error_message.lower() or "rate limit" in error_message.lower():
            # Rate limit errors - return 429 with retry info
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Please try again later. {error_message}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing transaction: {error_message}"
            )


@app.delete("/cache/{digest}")
async def clear_cache_entry(digest: str):
    """
    Clear a specific transaction from cache.
    
    Args:
        digest: Transaction digest to clear
        
    Returns:
        Success message
    """
    transaction_cache.delete(digest)
    return {"message": f"Cache cleared for {digest}"}


@app.delete("/cache")
async def clear_all_cache():
    """
    Clear all cached transactions.
    
    Returns:
        Success message with count
    """
    size = transaction_cache.size()
    transaction_cache.clear()
    return {"message": f"Cleared {size} cached transactions"}


# Serve frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"

if frontend_path.exists():
    # Mount static files first (needs to be before catch-all route)
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/app")
    async def serve_app():
        """Serve the frontend HTML at /app route."""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
