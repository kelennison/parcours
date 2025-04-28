import streamlit as st
import json

elements = [
    {"data": {"id": "node1", "label": "Node1"}},
    {"data": {"id": "node2", "label": "Node2"}},
    {"data": {"source": "node1", "target": "node2"}}
]

elements_json = json.dumps(elements)

cytoscape_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Graph</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.19.1/cytoscape.min.js"></script>
    <style>
        #cy {{
            width: 100%;
            height: 600px;
            position: relative;
            border: 1px solid #ccc;
        }}
        .node-editor {{
            position: absolute;
            background: white;
            padding: 2px 5px;
            border: 1px solid #0074D9;
            border-radius: 3px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            z-index: 9999;
            min-width: 60px;
            text-align: center;
        }}
        #newick-output {{
            margin-top: 10px;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .btn-container {{
            margin-top: 10px;
        }}
        .btn-container button {{
            margin-right: 5px;
            padding: 5px 10px;
        }}
        .selected-node {{
            background-color: #FF4136 !important;
            border: 2px solid #85144b !important;
        }}
        #selection-rectangle {{
            display: none;
            position: absolute;
            border: 2px dashed #0074D9;
            background-color: rgba(0, 116, 217, 0.1);
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div id="cy"></div>
    <div id="selection-rectangle"></div>
    <div class="btn-container">
        <button id="undo-btn">Undo</button>
        <button id="redo-btn">Redo</button>
        <button id="delete-btn">Delete Selected Node</button>
        <button id="duplicate-btn">Duplicate Selected</button> 
        <button id="reset-btn">Reset</button>  
        <button id="newick-btn">Generate Newick</button>
        <button id="download-btn">Download Newick</button>
    </div>
    <div id="newick-output"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var elements = {elements_json};
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'width': 30,
                            'height': 30,
                            'background-color': '#0074D9',
                            'label': 'data(label)',
                            'color': '#000',
                            'text-valign': 'bottom',
                            'text-halign': 'center',
                            'text-margin-y': 10,
                            'font-size': 10
                        }}
                    }},
                    // ADD THIS NEW STYLE RULE FOR SELECTED NODES
                    {{
                        selector: '.selected-node',
                        style: {{
                            'background-color': '#FF4136',
                            'border-width': 2,
                            'border-color': '#85144b',
                            'border-style': 'solid'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': '#000',
                            'target-arrow-color': '#000',
                            'target-arrow-shape': 'triangle',
                            'arrow-scale': 0.8
                        }}
                    }},
                    {{
                        selector: '.selected',
                        style: {{
                            'background-color': '#FF4136',
                            'width': 40,
                            'height': 40
                        }}
                    }}
                ],
                layout: {{
                    name: 'cose',
                    animate: false,
                    nodeDimensionsIncludeLabels: true
                }}
            }});

            let sourceNode = null;
            let activeEditor = null;
            let undoStack = [];
            let redoStack = [];
            let isUndoRedo = false;
            let selectedNodes = [];
            let isDragging = false;
            let startX, startY, currentX, currentY;
            
            // Initialize undo stack with initial state
            undoStack.push(cy.json().elements);

            // Save state on changes
            cy.on('add remove data', function(event) {{
                if (isUndoRedo) return;
                saveState();
            }});

            function saveState() {{
                var currentState = cy.json().elements;
                undoStack.push(currentState);
                redoStack = [];
            }}

            function applyState(state) {{
                isUndoRedo = true;
                // Cleanup active UI elements
                if (activeEditor) {{
                    activeEditor.remove();
                    activeEditor = null;
                }}
                if (sourceNode) {{
                    sourceNode.removeClass('selected');
                    sourceNode = null;
                }}
                // Replace elements
                cy.elements().remove();
                cy.add(state);
                isUndoRedo = false;
            }}

            function performUndo() {{
                if (undoStack.length < 2) return;
                var currentState = undoStack.pop();
                redoStack.push(currentState);
                var previousState = undoStack[undoStack.length - 1];
                applyState(previousState);
            }}

            function performRedo() {{
                if (redoStack.length === 0) return;
                var nextState = redoStack.pop();
                undoStack.push(nextState);
                applyState(nextState);
            }}


            // Reset functionality
            function performReset() {{
                isUndoRedo = true;
                
                // Cleanup UI elements
                if (activeEditor) {{
                    activeEditor.remove();
                    activeEditor = null;
                }}
                if (sourceNode) {{
                    sourceNode.removeClass('selected');
                    sourceNode = null;
                }}

                // Reset graph elements to the original 'elements'
                cy.elements().remove();
                cy.add(elements);  // Corrected from initialElements to elements
                
                // Reset layout
                cy.layout({{
                    name: 'cose',
                    animate: false,
                    nodeDimensionsIncludeLabels: true
                }}).run();

                // Reset history stacks to the original 'elements'
                undoStack = [elements];  // Corrected from initialElements to elements
                redoStack = [];
                
                isUndoRedo = false;
            }}
            
            
            // Drag selection functionality
            cy.on('mousedown', function(evt) {{
                if (evt.target === cy) {{
                    isDragging = true;
                    const containerRect = cy.container().getBoundingClientRect();
                    startX = evt.originalEvent.clientX - containerRect.left;
                    startY = evt.originalEvent.clientY - containerRect.top;
                    currentX = startX;
                    currentY = startY;
                    const rect = document.getElementById('selection-rectangle');
                    rect.style.display = 'block';
                    rect.style.left = startX + 'px';
                    rect.style.top = startY + 'px';
                    rect.style.width = '0';
                    rect.style.height = '0';
                }}
            }});

            cy.on('mousemove', function(evt) {{
                if (isDragging) {{
                    const containerRect = cy.container().getBoundingClientRect();
                    currentX = evt.originalEvent.clientX - containerRect.left;
                    currentY = evt.originalEvent.clientY - containerRect.top;
                    updateSelectionRectangle();
                }}
            }});

            function updateSelectionRectangle() {{
                const rect = document.getElementById('selection-rectangle');
                const left = Math.min(startX, currentX);
                const top = Math.min(startY, currentY);
                const width = Math.abs(currentX - startX);
                const height = Math.abs(currentY - startY);
                rect.style.left = left + 'px';
                rect.style.top = top + 'px';
                rect.style.width = width + 'px';
                rect.style.height = height + 'px';
            }}

            cy.on('mouseup', function(evt) {{
                if (isDragging) {{
                    isDragging = false;
                    const rect = document.getElementById('selection-rectangle');
                    rect.style.display = 'none';

                    const left = Math.min(startX, currentX);
                    const right = Math.max(startX, currentX);
                    const top = Math.min(startY, currentY);
                    const bottom = Math.max(startY, currentY);

                    const newSelected = cy.nodes().filter(node => {{
                        const pos = node.renderedPosition();
                        return pos.x >= left && pos.x <= right && pos.y >= top && pos.y <= bottom;
                    }});

                    selectedNodes.forEach(n => n.removeClass('selected-node'));
                    newSelected.addClass('selected-node');
                    selectedNodes = newSelected.toArray();
                }}
            }});
            // ====== FIXED SELECTION HANDLING ======
            cy.on('tap', 'node', function(evt) {{
                const node = evt.target;
                const isCtrl = evt.originalEvent.ctrlKey || evt.originalEvent.metaKey;

                // Clear selection if not holding Ctrl/Cmd
                if (!isCtrl && !node.hasClass('selected-node')) {{
                    selectedNodes.forEach(n => n.removeClass('selected-node'));
                    selectedNodes = [];
                }}

                // Toggle selection
                node.toggleClass('selected-node');
                if (node.hasClass('selected-node')) {{
                    selectedNodes.push(node);
                }} else {{
                    selectedNodes = selectedNodes.filter(n => n.id() !== node.id());
                }}
                evt.stopPropagation();
            }});

            // ====== DUPLICATE FUNCTION (with extra braces) ======
            document.getElementById('duplicate-btn').addEventListener('click', function() {{
                const selNodes = cy.nodes('.selected-node');
                if (selNodes.empty()) return;

                const selEdges = selNodes
                    .connectedEdges()
                    .filter(edge =>
                        selNodes.contains(edge.source()) &&
                        selNodes.contains(edge.target())
                    );
                
                const nodeJsons = selNodes.jsons();
                const edgeJsons = selEdges.jsons();

                const existing = new Set(cy.nodes().map(n => n.id()));
                let counter = 1;
                const idMap = new Map();
                nodeJsons.forEach(blob => {{
                    while (existing.has(`node${{counter}}`)) counter++;
                    const newId = `node${{counter++}}`;
                    existing.add(newId);
                    idMap.set(blob.data.id, newId);
                }});

                const newNodeBlobs = nodeJsons.map(blob => ({{
                    group: blob.group,
                    data: {{
                        ...blob.data,
                        id:    idMap.get(blob.data.id),
                        label: blob.data.label + '_copy'
                    }},
                    position: {{
                        x: blob.position.x + 50,
                        y: blob.position.y + 50
                    }}
                }}));

                const newEdgeBlobs = edgeJsons.map(blob => ({{
                    group: 'edges',  // Force group to edges
                    data: {{
                        ...blob.data,
                        id: `edge_${{idMap.get(blob.data.source)}}_${{idMap.get(blob.data.target)}}`, 
                        source: idMap.get(blob.data.source),
                        target: idMap.get(blob.data.target)
                    }}
                }}));
                cy.batch(() => {{
                    cy.add([...newNodeBlobs, ...newEdgeBlobs]);
                    saveState();
                }});
            }});


       
            // ====== DELETE FUNCTION (with extra braces) ======
            document.getElementById('delete-btn').addEventListener('click', function() {{  
                // 1. Exclude root  
                const toDelete = selectedNodes.filter(n => n.id() !== 'node1');  
                if (toDelete.length === 0) return;  

                // 2. Build collections  
                const nodeCollection = cy.collection(toDelete);  
                const edgeCollection = nodeCollection.connectedEdges();  

                // 3. Batch-remove & save state  
                cy.batch(() => {{  
                    cy.remove(edgeCollection);  
                    cy.remove(nodeCollection);  
                    saveState();  
                }});  

                // 4. Clear selection array (keep root if selected)  
                selectedNodes = selectedNodes.filter(n => n.id() === 'node1');  
            }});  


            // Node creation
            cy.on('tap', function(event) {{
                if (event.target === cy) {{
                    if (activeEditor) {{
                        activeEditor.remove();
                        activeEditor = null;
                    }}
                    if (sourceNode) {{
                        sourceNode.removeClass('selected');
                        sourceNode = null;
                    }}
                    var id = 'node' + (cy.nodes().length + 1);
                    cy.add({{
                        group: 'nodes',
                        data: {{ id: id, label: 'Node ' + (cy.nodes().length + 1) }},
                        position: {{ x: event.position.x, y: event.position.y }}
                    }});
                }}
            }});

            // Edge creation
            cy.on('tap', 'node', function(evt) {{
                if (activeEditor) return;
                
                const node = evt.target;
                if (!sourceNode) {{
                    sourceNode = node;
                    node.addClass('selected');
                }} else {{
                    if (sourceNode.id() !== node.id()) {{
                        cy.add({{
                            group: 'edges',
                            data: {{ source: sourceNode.id(), target: node.id() }}
                        }});
                    }}
                    sourceNode.removeClass('selected');
                    sourceNode = null;
                }}
            }});

            // Node editing
            cy.on('tap', 'node', function(evt) {{
                if (sourceNode || activeEditor) return;
                
                const node = evt.target;
                const position = node.renderedPosition();
                const bbox = node.renderedBoundingBox();
                
                if (activeEditor) activeEditor.remove();
                
                activeEditor = document.createElement('input');
                activeEditor.className = 'node-editor';
                activeEditor.value = node.data('label');
                
                activeEditor.style.left = (position.x - bbox.w/4) + 'px';
                activeEditor.style.top = (position.y + bbox.h/2 + 15) + 'px';
                activeEditor.style.width = bbox.w + 'px';
                
                cy.container().appendChild(activeEditor);
                activeEditor.focus();
                
                const save = () => {{
                    node.data('label', activeEditor.value);
                    activeEditor.remove();
                    activeEditor = null;
                }};
                
                activeEditor.addEventListener('blur', save);
                activeEditor.addEventListener('keydown', e => {{
                    if (e.key === 'Enter') save();
                }});
            }});

            

            // Cancel operations
            cy.on('tap', function(evt) {{
                if (evt.target === cy) {{
                    if (activeEditor) {{
                        activeEditor.remove();
                        activeEditor = null;
                    }}
                    if (sourceNode) {{
                        sourceNode.removeClass('selected');
                        sourceNode = null;
                    }}
                }}
            }});
            
            // Modified Newick generation function
            function generateNewick() {{
                // Always use Node1 as root
                const root = cy.$('#node1');
                if (root.length === 0) return "No root node found;";
                
                function traverse(node) {{
                    const children = node.outgoers().edges();
                    if (children.length === 0) {{
                        return `${{node.data('label')}}`; 
                    }}
                    
                    const childrenNewick = children.map(edge => {{
                        const child = edge.target();
                        return `${{traverse(child)}}`;
                    }}).join(',');
                    
                    return `(${{childrenNewick}})${{node.data('label')}}`;
                }}

                try {{
                    const newick = `${{traverse(root)}};`;
                    return newick;
                }} catch (e) {{
                    return "Invalid tree structure;";
                }}
            }}
            // Update Newick generation and add download handler
            document.getElementById('newick-btn').addEventListener('click', function() {{
                const newick = generateNewick();
                document.getElementById('newick-output').innerText = newick;
                window.parent.postMessage({{ type: 'newickOutput', newick: newick }}, '*');
            }});

            // Add download functionality
            document.getElementById('download-btn').addEventListener('click', function() {{
                const newick = generateNewick();
                const blob = new Blob([newick], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'tree.nh';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }});
            
            // Undo/Redo event listeners
            document.getElementById('undo-btn').addEventListener('click', performUndo);
            document.getElementById('redo-btn').addEventListener('click', performRedo);
            // Add event listener for reset button
            document.getElementById('reset-btn').addEventListener('click', performReset);
        }});
    </script>
</body>
</html>
"""

st.title("Newick Generation App")
st.components.v1.html(cytoscape_html, height=700)