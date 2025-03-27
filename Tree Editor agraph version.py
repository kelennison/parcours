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

    # Initialize session state
    if "nodes" not in st.session_state:
        st.session_state.nodes = []
    if "edges" not in st.session_state:
        st.session_state.edges = []

    # Newick format selector (moved up)
    newick_format = st.radio("Newick Format", ["With Branch Lengths", "Simplified (No Lengths)"], index=0)

    # Visualization section (needs to be before sidebar interactions)
    config = Config(
        width=800,
        height=600,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label"},
        clickable=True
    )
    
    # Render graph first
    response = agraph(nodes=st.session_state.nodes, 
                     edges=st.session_state.edges, 
                     config=config)

    # Handle node clicks and child addition
    if response:
        clicked_node = response
        with st.sidebar:
            st.subheader(f"Add Child to: {clicked_node}")
            new_child = st.text_input("Child Node ID", key=f"child_{clicked_node}")
            new_length = st.number_input("Branch Length", value=0.1, key=f"length_{clicked_node}")
            if st.button("Add Child Node"):
                if new_child:
                    # Add nodes/edges
                    st.session_state.nodes.append(Node(id=new_child, label=new_child))
                    st.session_state.edges.append(Edge(
                        source=clicked_node,
                        target=new_child,
                        label=f"{new_length:.2f}"
                    ))
                    st.rerun()  # Force immediate refresh

    # Manual node addition sidebar
    with st.sidebar:
        st.header("Manual Controls")
        parent = st.text_input("Parent Node ID (manual):")
        child = st.text_input("Child Node ID (manual):")
        branch_length = st.number_input("Branch Length (manual):", value=0.1)
        if st.button("Add Node Manually"):
            if child:
                st.session_state.nodes.append(Node(id=child, label=child))
                if parent:
                    st.session_state.edges.append(Edge(
                        source=parent,
                        target=child,
                        label=f"{branch_length:.2f}"
                    ))
                st.rerun()
        
        if st.button("Reset Tree"):
            st.session_state.nodes = []
            st.session_state.edges = []
            st.rerun()

    # Newick generation (moved after visualization)
    if st.button("Generate Newick"):
        nodes_dict = {}
        root = None
        for edge in st.session_state.edges:
            parent_id = edge.source  # Use .source instead of __dict__["from"]
            child_id = edge.to
            branch_length = float(edge.label)
            
            if parent_id not in nodes_dict:
                nodes_dict[parent_id] = TreeNode(name=parent_id, length=0.0)
                if not root:
                    root = nodes_dict[parent_id]
            if child_id not in nodes_dict:
                child_node = TreeNode(name=child_id, length=branch_length, parent=nodes_dict[parent_id])
                nodes_dict[parent_id].children.append(child_node)
                nodes_dict[child_id] = child_node
        
        if root:
            include_lengths = (newick_format == "With Branch Lengths")
            newick_str = generate_newick(root, include_lengths)
            st.code(f"{newick_str};", language="plaintext")
            st.download_button(
                "Download Newick",
                f"{newick_str};",
                "tree.nh",
                "text/plain"
            )
        else:
            st.warning("No tree detected!")

if __name__ == "__main__":
    main()