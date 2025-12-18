"""
Generate visual diagram data from transaction information.
"""
from typing import Dict, Any, List, Set
from .schemas import DiagramNode, DiagramEdge, DiagramData
from .utils import truncate_address


class DiagramGenerator:
    """Generate diagram data for transaction visualization."""
    
    def __init__(self, transaction_data: Dict[str, Any], parsed_data: Dict[str, Any]):
        """
        Initialize diagram generator.
        
        Args:
            transaction_data: Raw transaction data
            parsed_data: Parsed transaction data
        """
        self.transaction_data = transaction_data
        self.parsed_data = parsed_data
        self.nodes: List[DiagramNode] = []
        self.edges: List[DiagramEdge] = []
        self.node_ids: Set[str] = set()
    
    def _add_node(self, node_id: str, label: str, node_type: str) -> None:
        """
        Add a node if it doesn't exist.
        
        Args:
            node_id: Unique node identifier
            label: Display label
            node_type: Node type (address, object, package)
        """
        if node_id not in self.node_ids:
            self.nodes.append(DiagramNode(
                id=node_id,
                label=label,
                type=node_type
            ))
            self.node_ids.add(node_id)
    
    def _add_edge(self, source: str, target: str, label: str, edge_type: str) -> None:
        """
        Add an edge to the diagram.
        
        Args:
            source: Source node ID
            target: Target node ID
            label: Edge label
            edge_type: Edge type (transfer, mutation, creation, deletion)
        """
        self.edges.append(DiagramEdge(
            source=source,
            target=target,
            label=label,
            type=edge_type
        ))
    
    def generate(self) -> DiagramData:
        """
        Generate complete diagram data.
        
        Returns:
            DiagramData with nodes and edges
        """
        # Add sender node
        sender = self.parsed_data.get("sender")
        if sender:
            self._add_node(
                f"addr_{sender}",
                truncate_address(sender),
                "address"
            )
        
        # Add recipient nodes
        for recipient in self.parsed_data.get("recipients", []):
            self._add_node(
                f"addr_{recipient}",
                truncate_address(recipient),
                "address"
            )
        
        # Add package nodes
        for package in self.parsed_data.get("packages", []):
            package_id = package["package_id"]
            label = truncate_address(package_id)
            if package.get("module"):
                label = f"{package['module']}"
                if package.get("function"):
                    label += f"::{package['function']}"
            
            package_node_id = f"pkg_{package_id}"
            self._add_node(package_node_id, label, "package")
            
            # Connect sender to package
            if sender:
                self._add_edge(
                    f"addr_{sender}",
                    package_node_id,
                    "calls",
                    "mutation"
                )
        
        # Add edges for coin transfers
        for transfer in self.parsed_data.get("coin_transfers", []):
            address = transfer["address"]
            amount = transfer["amount"]
            formatted_amount = transfer["formatted_amount"]
            
            target_node = f"addr_{address}"
            
            if int(amount) > 0:
                # Receiving
                if sender:
                    self._add_edge(
                        f"addr_{sender}",
                        target_node,
                        f"+{formatted_amount}",
                        "transfer"
                    )
            else:
                # Sending (sender spending)
                pass  # Already covered by the positive amount to recipient
        
        # Add object nodes and edges
        object_changes = self.parsed_data.get("object_changes", {})
        
        # Created objects
        for obj in object_changes.get("created", []):
            obj_id = obj["object_id"]
            obj_node_id = f"obj_{obj_id}"
            
            # Extract simple type name
            obj_type = obj["object_type"]
            type_label = obj_type.split("::")[-1][:20]  # Last part, truncated
            
            self._add_node(obj_node_id, f"New: {type_label}", "object")
            
            # Connect from sender or package
            if sender:
                self._add_edge(
                    f"addr_{sender}",
                    obj_node_id,
                    "created",
                    "creation"
                )
            
            # Connect to owner if different from sender
            owner = obj.get("owner")
            if owner and owner != sender:
                owner_node = f"addr_{owner}"
                if owner.startswith("Object("):
                    # Object-owned
                    owner_id = owner[7:-1]
                    owner_node = f"obj_{owner_id}"
                    self._add_node(owner_node, truncate_address(owner_id), "object")
                
                self._add_edge(
                    obj_node_id,
                    owner_node,
                    "owned by",
                    "creation"
                )
        
        # Mutated objects
        for obj in object_changes.get("mutated", []):
            obj_id = obj["object_id"]
            obj_node_id = f"obj_{obj_id}"
            
            obj_type = obj["object_type"]
            type_label = obj_type.split("::")[-1][:20]
            
            self._add_node(obj_node_id, f"Modified: {type_label}", "object")
            
            if sender:
                self._add_edge(
                    f"addr_{sender}",
                    obj_node_id,
                    "modified",
                    "mutation"
                )
        
        # Deleted objects
        for obj in object_changes.get("deleted", []):
            obj_id = obj["object_id"]
            obj_node_id = f"obj_{obj_id}"
            
            obj_type = obj["object_type"]
            type_label = obj_type.split("::")[-1][:20]
            
            self._add_node(obj_node_id, f"Deleted: {type_label}", "object")
            
            if sender:
                self._add_edge(
                    f"addr_{sender}",
                    obj_node_id,
                    "deleted",
                    "deletion"
                )
        
        return DiagramData(nodes=self.nodes, edges=self.edges)


def generate_diagram(transaction_data: Dict[str, Any], parsed_data: Dict[str, Any]) -> DiagramData:
    """
    Generate diagram from transaction data.
    
    Args:
        transaction_data: Raw transaction data
        parsed_data: Parsed transaction data
        
    Returns:
        DiagramData for visualization
    """
    generator = DiagramGenerator(transaction_data, parsed_data)
    return generator.generate()
