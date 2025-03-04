import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config



class TreeNode:
    def __init__(self, name, length=0.0, parent=None):
        self.name = name
        self.length = length
        self.parent = parent
        self.children = []

def generate_newick(node, include_lengths=True):
    """Generate Newick with/without branch lengths"""
    if not node.children:
        return f"{node.name}:{node.length}" if include_lengths else node.name
    
    children_str = ",".join([generate_newick(child, include_lengths) for child in node.children])
    internal_part = f"{node.name}:{node.length}" if include_lengths else node.name
    return f"({children_str}){internal_part}"


def main():
    st.title("Visual Newick Tree Editor")

    # Initialize session state for nodes/edges
    if "nodes" not in st.session_state:
        st.session_state.nodes = []
    if "edges" not in st.session_state:
        st.session_state.edges = []

    # Add format selector
    newick_format = st.radio("Newick Format", ["With Branch Lengths", "Simplified (No Lengths)"], index=0)

    # Sidebar: Add Nodes/Edges
    with st.sidebar:
        st.header("Add Nodes")
        parent = st.text_input("Parent Node ID (optional):")
        child = st.text_input("Child Node ID:")
        branch_length = st.number_input("Branch Length:", min_value=0.0, value=0.1)
        if st.button("Add Node"):
            if child:
                # Add nodes/edges to session state
                st.session_state.nodes.append(Node(id=child, label=child))
                if parent:
                    st.session_state.edges.append(Edge(source=parent, target=child, label=f"{branch_length}"))

        # Reset tree
        if st.button("Reset Tree"):
            st.session_state.nodes = []
            st.session_state.edges = []

    # Visualize the tree using streamlit-agraph
    config = Config(
        width=800,
        height=600,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label"}
    )
    agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)

        # Generate Newick file (modified)
    if st.button("Generate Newick"):
        nodes_dict = {}
        root = None
        for edge in st.session_state.edges:
            # Use dictionary access for reserved keywords
            parent_id = edge.__dict__["from"]  # Direct access to "from" attribute
            child_id = edge.to
            branch_length = float(edge.label)
            
            # Create nodes using custom TreeNode class
            if parent_id not in nodes_dict:
                nodes_dict[parent_id] = TreeNode(name=parent_id,length =  0.0)
                if not root:
                    root = nodes_dict[parent_id]
            if child_id not in nodes_dict:
                child_node = TreeNode(name=child_id, length=branch_length, parent=nodes_dict[parent_id])
                nodes_dict[parent_id].children.append(child_node)
                nodes_dict[child_id] = child_node
        
        if root:
            include_lengths = (newick_format == "With Branch Lengths")
            newick_str = generate_newick(root, include_lengths)
            st.code(f"Newick String: {newick_str};", language="plaintext")
            
            # Download button
            download_str = f"{newick_str};"  # Explicit semicolon
            st.download_button(
                label="Download Newick File",
                data=download_str,
                file_name="tree.nh",
                mime="text/plain"
            )
        else:
            st.warning("No tree detected!")
if __name__ == "__main__":
    main()