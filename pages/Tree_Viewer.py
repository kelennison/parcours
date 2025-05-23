import streamlit as st
import tempfile
import subprocess
import os

def visualize_tree(newick_file):
    """Run the R visualization script and display results"""
    try:
        # Run R script
        result = subprocess.run(
            ["Rscript", 
             "treeviewer.R", 
             newick_file],  # Fixed variable name
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Display generated image
            st.image("Rplot.png", caption="Phylogenetic Tree Visualization", use_column_width=True)
        else:
            st.error("Error generating visualization:")
            st.code(result.stderr)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


def main():
    st.title("Phylogenetic Tree Viewer")
    
    # Input options
    input_method = st.radio("Input method:", 
                           ("Upload .nh file", "Paste Newick string"))
    
    newick_str = None
    temp_file = None
    
    if input_method == "Upload .nh file":
        uploaded_file = st.file_uploader("Choose a Newick file", type=["nh", "tree"])
        if uploaded_file:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".nh") as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_file = tmp.name
    
    else:  # Paste Newick string
        newick_str = st.text_area("Paste your Newick string:", height=150,
                                 help="Example: (A:0.1,B:0.2,(C:0.3,D:0.4):0.5);")
        if newick_str:
            # Validate and save to temporary file
            if not newick_str.strip().endswith(';'):
                st.warning("Warning: Newick string should end with semicolon (;)")
                
            with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".nh") as tmp:
                tmp.write(newick_str)
                temp_file = tmp.name
    
    # Visualization button
    if temp_file and st.button("Visualize Tree"):
        st.subheader("Tree Visualization")
        with st.spinner("Generating visualization..."):
            visualize_tree(temp_file)
        
        # Clean up temporary file
        try:
            os.remove(temp_file)
        except:
            pass

if __name__ == "__main__":
    main()