/**
 * Diagram rendering using Cytoscape.js
 */

let cy = null; // Cytoscape instance

/**
 * Render transaction diagram
 */
function renderDiagram(diagramData) {
    const container = document.getElementById('diagramContainer');
    
    if (!diagramData || !diagramData.nodes || diagramData.nodes.length === 0) {
        container.innerHTML = '<p class="empty-message">No diagram data available</p>';
        return;
    }
    
    // Clear previous diagram
    container.innerHTML = '';
    
    // Prepare elements for Cytoscape
    const elements = [
        ...diagramData.nodes.map(node => ({
            data: {
                id: node.id,
                label: node.label,
                type: node.type
            }
        })),
        ...diagramData.edges.map(edge => ({
            data: {
                id: `${edge.source}-${edge.target}-${Math.random()}`,
                source: edge.source,
                target: edge.target,
                label: edge.label,
                type: edge.type
            }
        }))
    ];
    
    // Initialize Cytoscape
    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            // Node styles
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px',
                    'color': '#fff',
                    'text-outline-width': 2,
                    'text-outline-color': '#333',
                    'width': '60px',
                    'height': '60px',
                    'border-width': 2,
                    'border-color': '#fff'
                }
            },
            // Address nodes
            {
                selector: 'node[type="address"]',
                style: {
                    'background-color': '#4A90E2',
                    'shape': 'ellipse'
                }
            },
            // Object nodes
            {
                selector: 'node[type="object"]',
                style: {
                    'background-color': '#7B68EE',
                    'shape': 'rectangle'
                }
            },
            // Package nodes
            {
                selector: 'node[type="package"]',
                style: {
                    'background-color': '#50C878',
                    'shape': 'hexagon'
                }
            },
            // Edge styles
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#999',
                    'target-arrow-color': '#999',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'text-background-color': '#fff',
                    'text-background-opacity': 0.8,
                    'text-background-padding': '3px',
                    'color': '#333'
                }
            },
            // Transfer edges (coin transfers)
            {
                selector: 'edge[type="transfer"]',
                style: {
                    'line-color': '#4CAF50',
                    'target-arrow-color': '#4CAF50',
                    'width': 4
                }
            },
            // Mutation edges
            {
                selector: 'edge[type="mutation"]',
                style: {
                    'line-color': '#FF9800',
                    'target-arrow-color': '#FF9800'
                }
            },
            // Creation edges
            {
                selector: 'edge[type="creation"]',
                style: {
                    'line-color': '#2196F3',
                    'target-arrow-color': '#2196F3',
                    'line-style': 'dashed'
                }
            },
            // Deletion edges
            {
                selector: 'edge[type="deletion"]',
                style: {
                    'line-color': '#F44336',
                    'target-arrow-color': '#F44336',
                    'line-style': 'dotted'
                }
            }
        ],
        layout: {
            name: 'breadthfirst',
            directed: true,
            padding: 30,
            spacingFactor: 1.5,
            animate: true,
            animationDuration: 500
        },
        wheelSensitivity: 0.2,
        minZoom: 0.3,
        maxZoom: 3
    });
    
    // Add interaction behaviors
    addDiagramInteractions();
}

/**
 * Add interactive behaviors to diagram
 */
function addDiagramInteractions() {
    if (!cy) return;
    
    // Highlight connected elements on hover
    cy.on('mouseover', 'node', function(event) {
        const node = event.target;
        
        // Highlight the node
        node.addClass('highlighted');
        
        // Highlight connected edges
        node.connectedEdges().addClass('highlighted');
        
        // Highlight connected nodes
        node.neighborhood('node').addClass('highlighted');
    });
    
    cy.on('mouseout', 'node', function(event) {
        const node = event.target;
        
        // Remove highlights
        node.removeClass('highlighted');
        node.connectedEdges().removeClass('highlighted');
        node.neighborhood('node').removeClass('highlighted');
    });
    
    // Show tooltip on tap/click
    cy.on('tap', 'node', function(event) {
        const node = event.target;
        const data = node.data();
        
        alert(
            `Node Information:\n\n` +
            `ID: ${data.id}\n` +
            `Label: ${data.label}\n` +
            `Type: ${data.type}`
        );
    });
    
    // Add highlight styles
    cy.style()
        .selector('.highlighted')
        .style({
            'background-color': '#FFD700',
            'line-color': '#FFD700',
            'target-arrow-color': '#FFD700',
            'transition-property': 'background-color, line-color, target-arrow-color',
            'transition-duration': '0.3s'
        })
        .update();
    
    // Fit diagram to container
    cy.fit(50);
    cy.center();
}

/**
 * Export diagram as image (optional feature)
 */
function exportDiagramAsImage() {
    if (!cy) return;
    
    const png64 = cy.png({
        output: 'base64',
        bg: 'white',
        full: true,
        scale: 2
    });
    
    // Create download link
    const link = document.createElement('a');
    link.href = png64;
    link.download = 'transaction-diagram.png';
    link.click();
}

/**
 * Reset diagram view
 */
function resetDiagramView() {
    if (!cy) return;
    
    cy.fit(50);
    cy.center();
}

/**
 * Change diagram layout
 */
function changeDiagramLayout(layoutName) {
    if (!cy) return;
    
    const layouts = {
        'breadthfirst': {
            name: 'breadthfirst',
            directed: true,
            padding: 30,
            spacingFactor: 1.5
        },
        'circle': {
            name: 'circle',
            padding: 30,
            spacingFactor: 1.5
        },
        'grid': {
            name: 'grid',
            padding: 30,
            spacingFactor: 1.5
        },
        'cose': {
            name: 'cose',
            padding: 30,
            nodeRepulsion: 400000,
            idealEdgeLength: 100
        }
    };
    
    const layout = layouts[layoutName] || layouts['breadthfirst'];
    cy.layout({
        ...layout,
        animate: true,
        animationDuration: 500
    }).run();
}
