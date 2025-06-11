import streamlit as st
import json

elements = [
    {"data": {"id": "node1", "label": "Root"}},
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
            position: fixed;
            background: white;
            padding: 2px 5px;
            border: 1px solid #0074D9;
            border-radius: 3px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            z-index: 1000;
            min-width: 60px;
            text-align: center;
        }}
        #newick-output {{
            margin-top: 10px;
            font-family: monospace;
            white-space: pre-wrap;
            font-size: 14px; 
            min-height: 60px;
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
            z-index: 9999
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
        <div id="newick-output"></div>
        <div id="edge-warning" style="margin-top:10px; color:red; font-family: monospace; font-size: 14px;"></div>

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
                            'label': 'data(label)',
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
                    
                    
                ],
                layout: {{
                    name: 'cose',
                    animate: false,
                    nodeDimensionsIncludeLabels: true
                }}

            }});

        // ==== GROUP DRAGGING FOR SELECTED NODES ====
        let initialPositions = new Map();
        let isGroupDragging = false;

        cy.on('grab', 'node', function(evt) {{
            const node = evt.target;
            if (node.hasClass('selected-node')) {{
                isGroupDragging = true;
                // Store initial positions of all selected nodes
                selectedNodes.forEach(n => {{
                    initialPositions.set(n.id(), {{
                        x: n.position('x'),
                        y: n.position('y')
                    }});
                }});
            }}
        }});

        cy.on('drag', 'node', function(evt) {{
            if (!isGroupDragging) return;

            const draggedNode = evt.target;
            if (!draggedNode.hasClass('selected-node')) return;

            // Calculate displacement
            const dx = draggedNode.position('x') - initialPositions.get(draggedNode.id()).x;
            const dy = draggedNode.position('y') - initialPositions.get(draggedNode.id()).y;

            // Move all selected nodes by the same displacement
            selectedNodes.forEach(n => {{
                if (n.id() !== draggedNode.id()) {{
                    n.position({{
                        x: initialPositions.get(n.id()).x + dx,
                        y: initialPositions.get(n.id()).y + dy
                    }});
                }}
            }});
        }});

        cy.on('free', 'node', function() {{
            isGroupDragging = false;
            initialPositions.clear();
        }});

            
            // ─── only mark justDragged when a real box‐selection occurred ──────────
            cy.boxSelectionEnabled(true);
            cy.on('boxselect', function() {{
                justDragged = true;
            }});
   
            let sourceNode = null;
            let activeEditor = null;
            let undoStack = [];
            let redoStack = [];
            let isUndoRedo = false;
            let selectedNodes = [];
            let isDragging = false;
            let startX, startY, currentX, currentY;
            let justDragged = false;
            
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
                    evt.originalEvent.preventDefault(); 
                    cy.userPanningEnabled(false);
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
                    evt.originalEvent.preventDefault();
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

           // ====== FIXED DRAG SELECT ON MOUSEUP ======
            cy.on('mouseup', function(evt) {{
                if (isDragging) {{
                    cy.userPanningEnabled(true);
                    cy.nodes().ungrabify(false);  // Enable node dragging
                    isDragging = false;

                    // hide the marquee
                    const rect = document.getElementById('selection-rectangle');
                    rect.style.display = 'none';

                    // compute bounds
                    const left   = Math.min(startX, currentX);
                    const right  = Math.max(startX, currentX);
                    const top    = Math.min(startY, currentY);
                    const bottom = Math.max(startY, currentY);

                    // select nodes in box
                    const newSelected = cy.nodes().filter(node => {{
                        const pos = node.renderedPosition();
                        return pos.x >= left && pos.x <= right
                            && pos.y >= top  && pos.y <= bottom;
                    }});

                    // clear old, apply new
                    selectedNodes.forEach(n => n.removeClass('selected-node'));
                    newSelected.addClass('selected-node');
                    selectedNodes = newSelected.toArray();

                    // block the normal blank‑space tap → node creation
                    evt.stopPropagation();
                    evt.originalEvent.preventDefault();
                    return false;
                }}
            }});

                        
            // ====== FIXED CTRL CLICK TOGGLE ======
            cy.on('tap', 'node', function(evt) {{
                const node = evt.target;
                const isCtrl = evt.originalEvent.ctrlKey || evt.originalEvent.metaKey;
                // KEY FIX: Skip if it's the first tap of a double-tap
                if (evt.originalEvent.detail >= 2) return;

                // 1. If no Ctrl/Cmd, clear prior selection
                if (!isCtrl && !node.hasClass('selected-node')) {{
                    selectedNodes.forEach(n => n.removeClass('selected-node'));
                    selectedNodes = [];
                }}

                // 2. Toggle the clicked node’s selected‑state
                node.toggleClass('selected-node');
                if (node.hasClass('selected-node')) {{
                    selectedNodes.push(node);
                }} else {{
                    selectedNodes = selectedNodes.filter(n => n.id() !== node.id());
                }}

                // 3. Prevent any downstream tap handlers (like node‑creation) from firing
                evt.stopPropagation();
                evt.originalEvent.preventDefault();
                return false;
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
                        id: idMap.get(blob.data.id),
                        label: blob.data.label + '_copy'
                    }},
                    position: {{
                        x: blob.position.x + 200,
                        y: blob.position.y + 150
                    }}
                }}));

                const newEdgeBlobs = edgeJsons.map(blob => ({{
                    group: 'edges',
                    data: {{
                        ...blob.data,
                        id: `edge_${{idMap.get(blob.data.source)}}_${{idMap.get(blob.data.target)}}`,
                        source: idMap.get(blob.data.source),
                        target: idMap.get(blob.data.target)
                    }}
                }}));

                cy.batch(() => {{
                    const newEles = cy.add([...newNodeBlobs, ...newEdgeBlobs]);

                    // 1. Clear old selection
                    cy.nodes('.selected-node').removeClass('selected-node');
                    selectedNodes = [];

                    // 2. Select only new duplicated nodes
                    const newNodes = newEles.filter(ele => ele.isNode());
                    newNodes.forEach(n => n.addClass('selected-node'));
                    selectedNodes = newNodes.toArray();

                    saveState();
                }});
            }});

            // ====== IMPROVED DELETE FUNCTION — with interaction reset ======
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

                // 4. Clear selection state
                selectedNodes = selectedNodes.filter(n => n.id() === 'node1'); 
                cy.nodes('.selected-node').removeClass('selected-node');
                selectedNodes = [];
                sourceNode = null;

                // 5. Reset interaction flags and selection visuals
                isDragging = false;
                justDragged = false;
                cy.userPanningEnabled(true);
                document.getElementById('selection-rectangle').style.display = 'none';
            }});
  
            

            // ─── REVISED TAP handler: now checks justDragged first ────────────────
            cy.on('tap', function(event) {{
                if (event.target === cy) {{
                    cy.userPanningEnabled(true);  // ✅ Re-enable panning
                    // 1) Swallow *only* the stray tap that follows a box‐select
                    if (justDragged) {{
                        justDragged = false;
                        return false;
                    }}

                    // 2) If any nodes are selected, deselect them
                    const selected = cy.nodes('.selected-node');
                    if (selected.length > 0) {{
                        selected.removeClass('selected-node');
                        selectedNodes = [];
                        event.stopImmediatePropagation();
                        event.preventDefault();
                        return false;
                    }}

                    // 3) Cleanup editors/edge‐creation
                    if (activeEditor) {{
                        activeEditor.remove();
                        activeEditor = null;
                        return;
                    }}
                    if (sourceNode) {{
                        sourceNode.removeClass('selected');
                        sourceNode = null;
                        return;
                    }}

                    // 4) Finally: create a new node
                    const id = 'node' + (cy.nodes().length + 1);
                    cy.add({{
                        group: 'nodes',
                        data: {{ id: id, label: 'Node ' + (cy.nodes().length + 1) }},
                        position: event.position
                    }});
                }}
            }});

            // Escape key handler
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    const selected = cy.nodes('.selected-node');
                    selected.removeClass('selected-node');
                    selectedNodes = [];
                }}
            }});
            

            // ==== MODIFIED EDGE CREATION HANDLER - PREVENTS DUPLICATE EDGES ====
            cy.on('tap', 'node', function(evt) {{
                if (activeEditor) return;

                const node = evt.target;
                if (!sourceNode) {{
                    sourceNode = node;
                    node.addClass('selected-node');
                    evt.stopImmediatePropagation();
                }} else {{
                    if (sourceNode.id() !== node.id()) {{
                        // Check if edge already exists
                        const existingEdge = cy.edges().filter(edge => 
                            (edge.data('source') === sourceNode.id() && 
                            edge.data('target') === node.id()) ||
                            (edge.data('source') === node.id() && 
                            edge.data('target') === sourceNode.id())
                        );

                        if (existingEdge.length === 0) {{
                            cy.add({{
                                group: 'edges',
                                data: {{ source: sourceNode.id(), target: node.id() }}
                            }});
                        }} else {{
                            document.getElementById('edge-warning').innerText = "Edge already exists between these nodes!";
                            setTimeout(() => {{
                                document.getElementById('edge-warning').innerText = "";
                            }}, 10000);  // Hide after 10 seconds

                        }}
                    }}
                    // Clear ALL selections after edge creation
                    cy.nodes('.selected-node').removeClass('selected-node');
                    selectedNodes = [];
                    sourceNode = null;
                    evt.stopImmediatePropagation();
                }}
            }});

            
            var lastClickTime = 0;
            var clickTimeout;
            var DOUBLE_CLICK_DELAY = 300;

            cy.on('click', 'node', function(evt) {{
            var currentTime = new Date().getTime();
            if (currentTime - lastClickTime < DOUBLE_CLICK_DELAY) {{
                evt.stopImmediatePropagation();
                evt.preventDefault();
                
                const node = evt.target;
                // Clear existing selections and highlight current node
                selectedNodes.forEach(n => n.removeClass('selected-node'));
                selectedNodes = [node];
                node.addClass('selected-node');
                
                const position = node.renderedPosition();
                const bbox = node.renderedBoundingBox();
                
                if (activeEditor) {{
                    activeEditor.remove();
                    activeEditor = null;
                }}
                
                activeEditor = document.createElement('input');
                activeEditor.className = 'node-editor';
                activeEditor.value = node.data('label');
                
                activeEditor.style.left = (position.x - bbox.w/4) + 'px';
                activeEditor.style.top = (position.y + bbox.h/2 + 15) + 'px';
                activeEditor.style.width = bbox.w + 'px';
                
                cy.container().appendChild(activeEditor);
                activeEditor.focus();
                activeEditor.select();
                
                // In the double-click handler's save function
                const save = () => {{
                    node.data('label', activeEditor.value);
                    activeEditor.remove();
                    activeEditor = null;
                    
                    // Clear ALL selection classes and edge-creation state
                    cy.nodes('.selected-node').removeClass('selected-node');
                    selectedNodes = [];
                    
                    // Critical: Reset edge-creation source node
                    if (sourceNode) {{
                        sourceNode.removeClass('selected-node');
                        sourceNode = null;
                    }}
                }};
                
                activeEditor.addEventListener('blur', save);
                activeEditor.addEventListener('keydown', e => {{
                    if (e.key === 'Enter'){{
                        e.stopPropagation()
                      save();
                    }}
                }});
            }}
            lastClickTime = currentTime;
            }});
           
            // ====== ADVANCED ROOT-DETECTING, VISUAL-ORDERED NEWICK GENERATION ======
            function generateNewick() {{
                try {{
                    // Helper: explore connected nodes (undirected)
                    function explore(node, visited) {{
                        if (visited.has(node.id())) return;
                        visited.add(node.id());
                        node.connectedEdges().forEach(edge => {{
                            const neighbor = edge.source().id() === node.id()
                                ? edge.target()
                                : edge.source();
                            explore(neighbor, visited);
                        }});
                    }}

                    // Helper: pick the node that reaches the most others
                    function findRootCandidate() {{
                        const scores = new Map();
                        cy.nodes().forEach(node => {{
                            const reachable = new Set();
                            explore(node, reachable);
                            scores.set(node.id(), reachable.size);
                        }});
                        let maxNode = null;
                        let maxReach = -1;
                        for (let [id, score] of scores.entries()) {{
                            if (score > maxReach) {{
                                maxNode = cy.getElementById(id);
                                maxReach = score;
                            }}
                        }}
                        return maxNode;
                    }}

                    const root = findRootCandidate();
                    if (!root) return "Could not determine root node.";

                    const visited = new Set();

                    // Recursive Newick builder
                    function traverse(node) {{
                        if (visited.has(node.id())) {{
                            throw new Error("Cycle detected");
                        }}
                        visited.add(node.id());

                        // Get all undirected neighbors not yet visited
                        const neighbors = node.connectedEdges()
                            .map(edge => {{
                                return edge.source().id() === node.id()
                                    ? edge.target()
                                    : edge.source();
                            }})
                            .filter(n => !visited.has(n.id()))
                            .sort((a, b) => a.renderedPosition().y - b.renderedPosition().y); // 🔥 sort visually top-down

                        const childrenStrings = neighbors.map(n => traverse(n));

                        if (childrenStrings.length > 0) {{
                            return `(${{childrenStrings.join(',')}})${{node.data('label')}}`;
                        }}
                        return node.data('label');
                    }}

                    const newick = `${{traverse(root)}};`;
                    return newick;

                }} catch (e) {{
                    return "Newick generation failed: " + e.message;
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
st.components.v1.html(cytoscape_html, height=1000)