"""
Pydantic models for request/response validation.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request model for transaction analysis."""
    digest: str = Field(..., description="Sui transaction digest to analyze")


class DiagramNode(BaseModel):
    """Node in the transaction diagram."""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label for the node")
    type: str = Field(..., description="Node type: address, object, or package")


class DiagramEdge(BaseModel):
    """Edge in the transaction diagram."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(..., description="Edge label describing the relationship")
    type: str = Field(..., description="Edge type: transfer, mutation, creation, deletion")


class DiagramData(BaseModel):
    """Transaction diagram structure."""
    nodes: List[DiagramNode] = Field(default_factory=list, description="List of nodes")
    edges: List[DiagramEdge] = Field(default_factory=list, description="List of edges")


class ObjectChange(BaseModel):
    """Represents a change to a Sui object."""
    object_id: str = Field(..., description="Object ID")
    object_type: Optional[str] = Field(None, description="Full object type")
    owner: Optional[str] = Field(None, description="Owner address")
    digest: Optional[str] = Field(None, description="Object digest")
    version: Optional[str] = Field(None, description="Object version")
    
    model_config = {"coerce_numbers_to_str": True}
    
    @classmethod
    def model_validate(cls, obj):
        # Convert version to string if it's a number
        if isinstance(obj, dict) and "version" in obj and obj["version"] is not None:
            obj["version"] = str(obj["version"])
        return super().model_validate(obj)


class ObjectChanges(BaseModel):
    """Collection of object changes."""
    created: List[ObjectChange] = Field(default_factory=list, description="Created objects")
    mutated: List[ObjectChange] = Field(default_factory=list, description="Mutated objects")
    deleted: List[ObjectChange] = Field(default_factory=list, description="Deleted objects")


class PackageInfo(BaseModel):
    """Information about a Move package involved in the transaction."""
    package_id: str = Field(..., description="Package ID")
    module: Optional[str] = Field(None, description="Module name")
    function: Optional[str] = Field(None, description="Function name")


class AnalyzeResponse(BaseModel):
    """Response model for transaction analysis."""
    summary: str = Field(..., description="Human-readable explanation of the transaction")
    diagram: DiagramData = Field(..., description="Visual diagram data")
    objects: ObjectChanges = Field(..., description="Object changes in the transaction")
    packages: List[PackageInfo] = Field(default_factory=list, description="Packages involved")
    gas_used: str = Field(..., description="Gas used in SUI")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw transaction data for debugging")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
