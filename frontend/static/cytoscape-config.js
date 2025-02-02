const cytoscapeConfig = {
    style: [
        {
            selector: 'node',
            style: {
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '12px',
                'color': '#374151',
                'text-wrap': 'wrap',
                'text-max-width': '80px',
                'background-color': '#fff',
                'border-width': 2,
                'border-color': '#d1d5db',
                'width': 40,
                'height': 40
            }
        },
        {
            selector: 'node[type="server"]',
            style: {
                'shape': 'rectangle',
                'border-color': '#3b82f6',
                'background-color': '#eff6ff'
            }
        },
        {
            selector: 'node[type="switch"]',
            style: {
                'shape': 'diamond',
                'border-color': '#10b981',
                'background-color': '#ecfdf5'
            }
        },
        {
            selector: 'edge',
            style: {
                'width': 2,
                'line-color': '#9ca3af',
                'target-arrow-color': '#9ca3af',
                'curve-style': 'bezier'
            }
        },
        {
            selector: 'edge[status="active"]',
            style: {
                'line-color': '#10b981',
                'target-arrow-color': '#10b981'
            }
        }
    ],
    layout: {
        name: 'cose',
        padding: 50,
        nodeRepulsion: 8000,
        idealEdgeLength: 100
    },
    wheelSensitivity: 0.2
};
