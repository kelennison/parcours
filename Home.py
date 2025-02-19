from ete3 import Tree
import streamlit as st
import subprocess
import sys
import os
import zipfile
import pandas as pd
import glob
from PIL import Image
from ete3 import Tree
import pandas as pd
import os
import tempfile
import ete3
import shutil  # Import shutil for file copying


# Page setup
st.set_page_config(layout="wide")
st.title('Parcours: Correlated Evolution Analysis')

# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style/style.css")  # Load your existing CSS file


# Function to perform data wrangling on the pairwise file and extract subtree
def wrangle_pairwise_data(tree_path):
    pairwise_path = "pairwise.csv"
    if os.path.exists(pairwise_path):
        # Load the CSV file
        df = pd.read_csv(pairwise_path)

        # Filter rows where Correlation is greater than or equal to 0.5
        #df = df[df['Correlation'] >= 0.5]

        # Exclude rows where Transition_2 is "unknown" or Char_1 and Char_2 contain "BodyLength"
        df = df[
            (df['Transition_2'] != 'unknown') &
            (~df['Char_1'].str.contains('BodyLength')) &
            (~df['Char_2'].str.contains('BodyLength'))
        ]

        # Further filtering for unknown values in Transition_1 and Transition_2
        df = df[~df['Transition_1'].str.contains('unknown', na=False) &
                ~df['Transition_2'].str.contains('unknown', na=False)]

        # Select relevant columns
        df = df[['Char_1', 'Char_2', 'Transition_1',
                 'Transition_2', 'C_Map_1', 'C_Map_2']]

        # Clean Char_1 and Char_2 columns
        # for col in ['Char_1', 'Char_2']:
        #   df[col] = df[col].str.replace(r'^[AB]\.', '', regex=True)
        #  df[col] = df[col].str.replace(r'-.*', '', regex=True).str.strip()

        # Clean Transition_1, Transition_2, C_Map_1, C_Map_2 columns
        for col in ['Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2']:
            df[col] = df[col].str.replace(' ', '', regex=False)

        # Replace 'absent' and 'present' with 0 and 1
        df['Transition_1'] = df['Transition_1'].str.replace(
            'absent', '0').str.replace('present', '1')
        df['Transition_2'] = df['Transition_2'].str.replace(
            'absent', '0').str.replace('present', '1')

        # Create a new merged index column
        df['Merged_Index'] = df['Char_1'] + " - " + df['Char_2']
        df = df.set_index('Merged_Index')

        # Save the wrangled data
        wrangled_pairwise_path = "wrangled_pairwise.csv"
        df.to_csv(wrangled_pairwise_path, index=False)

        # Return the processed dataframe and path
        return df, wrangled_pairwise_path, "subtree_output_path"
    return None, None, None


# File upload widgets for required files
st.write('Upload your phylogenetic tree and character state data:')
extant_file = st.file_uploader("Choose extant state file", type=["csv"])
tree_file = st.file_uploader(
    "Choose phylogenetic tree file", type=["nh", "tree"])

# Use hard-coded paths for config and physical files
config_file_path = r"assets\config1.csv"
fixed_physical_file_path = r"physical.csv"


# Store it in the session state
st.session_state["config_file_path"] = config_file_path

if tree_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".nh") as tmp:
        tmp.write(tree_file.getvalue())
        st.session_state.tree_file_path = tmp.name  # Store path in session state

# Initialize optional files
cost_file = None


# Function to check if specific files are referenced in the config file
def check_file_in_config(file_path, keyword):
    if file_path:
        config_data = pd.read_csv(file_path)
        # Flatten data to check for the presence of keywords
        if keyword in config_data.to_string().lower():
            return True
    return False


if os.path.exists(config_file_path):
    if check_file_in_config(config_file_path, 'cost.csv'):
        st.write("Cost file is mentioned in the config file, automatically adding it to the list.")
        cost_file = st.file_uploader("Upload cost file", type=["csv"])


# Set the Python interpreter path
python_path = sys.executable

# Function to clear output files
def clear_output_files():
    files_to_remove = glob.glob(
        "*.csv") + glob.glob("*.nexus") + glob.glob("solutions/*")
    for file_path in files_to_remove:
        os.remove(file_path)


# Variable to check if analysis has been completed and wrangled data exists
analysis_completed = False
wrangled_pairwise_path = None


# Button to run analysis with a spinner
if st.button('Run Analysis'):
    # Ensure all required files are present
    if extant_file and tree_file:
        # Clear previous output files
        clear_output_files()

        with open("extant.csv", "wb") as f:
            f.write(extant_file.getbuffer())
        with open("tree.nh", "wb") as f:
            f.write(tree_file.getbuffer())
        # Save optional files if uploaded
        if cost_file:
            with open("cost.csv", "wb") as f:
                f.write(cost_file.getbuffer())
         # Check if the fixed physical file exists
        if not os.path.exists(fixed_physical_file_path):
            st.error(f"Physical file not found at: {fixed_physical_file_path}")
        else:
            # Copy the fixed physical file to the working directory as 'physical.csv'
            shutil.copy(fixed_physical_file_path, "physical.csv")
            

        # Define paths
        parcours_script = r"parcours.py"

        command = [python_path, parcours_script,
                       "-f", config_file_path,
                       "-t", "tree.nh",
                       "-e", "extant.csv"]

            # Include optional cost file if provided
        if cost_file:
            command += ["-c", "cost.csv"]

            # Pass the physical file now in the working directory
        command += ["-p", "pairwise.csv"]

        # Run analysis with spinner
        with st.spinner("Running analysis..."):
            result = subprocess.run(command, capture_output=True, text=True)

        # Display results
        if result.returncode == 0:
            st.success("Analysis completed successfully!")
            st.write(result.stdout)
             # load the raw pairwise data and store it in session state.
            if os.path.exists("pairwise.csv"):
                raw_df = pd.read_csv("pairwise.csv")
                st.session_state.raw_pairwise_df = raw_df
            else:
                st.error("pairwise.csv not found!")

            # Proceed to wrangle data after successful analysis
            df, wrangled_pairwise_path, subtree_path = wrangle_pairwise_data(
                "tree.nh")
            analysis_completed = True  # Set flag to indicate analysis is completed

            # Collect output files and check existence before adding them to the ZIP
            output_files = ["output.csv",
                            "pairwise.csv", "unit.csv", "solns.csv"]
            output_dir = "solutions"
            output_files.extend([os.path.join(output_dir, f) for f in os.listdir(
                output_dir) if os.path.isfile(os.path.join(output_dir, f))])
            
            if wrangled_pairwise_path:
                    output_files.append(wrangled_pairwise_path)

            # Include wrangled pairwise CSV in the output files
            output_files.append(wrangled_pairwise_path)

            # Zip the output files
            zip_path = "analysis_results.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in output_files:
                    if os.path.exists(file):  # Only add the file if it exists
                        zipf.write(file)

            # Provide a download button for the zip file with spinner
            with open(zip_path, "rb") as f:
                with st.spinner("Preparing download..."):
                    st.download_button(
                        label="Download Analysis Results",
                        data=f,
                        file_name=zip_path,
                        mime="application/zip"
                    )
        else:
            st.error("Error running analysis.")
            st.write("Return code:", result.returncode)
            st.write("Standard Output:", result.stdout)
            st.write("Standard Error:", result.stderr)
    else:
        st.error("Please upload all required files.")


def preserve_relevant_nodes(tree, annotated_leaves):
    nodes_to_preserve = set()

    for leaf_name in annotated_leaves:
        # Find the target node
        target_node = tree.search_nodes(name=leaf_name)[0]
        nodes_to_preserve.add(target_node)

        # Traverse up and preserve parents and siblings
        current_node = target_node.up
        while current_node:
            nodes_to_preserve.add(current_node)

            # Preserve siblings of the current node
            for sibling in current_node.children:
                nodes_to_preserve.add(sibling)

            current_node = current_node.up

    # Return a list of nodes to preserve for later use
    return nodes_to_preserve


def collapse_irrelevant_nodes(tree, nodes_to_preserve):
    for node in tree.traverse("postorder"):
        if node not in nodes_to_preserve and not node.is_leaf():
            node.delete(prevent_nondicotomic=False)

    # Remove unnecessary single-child nodes
    tree.prune([n.name for n in nodes_to_preserve if n.name])
    return tree


def preserve_nodes_and_find_subtree(tree, annotated_leaves, node_threshold=30):
    # Step 1: Explicitly mark nodes to preserve
    nodes_to_preserve = set()
    for leaf_name in annotated_leaves:
        target_node = tree.search_nodes(name=leaf_name)[0]
        nodes_to_preserve.add(target_node)
        current_node = target_node.up
        while current_node:
            nodes_to_preserve.add(current_node)
            nodes_to_preserve.update(
                current_node.children)  # Preserve siblings
            current_node = current_node.up

    # Step 2: Identify the LCA of all annotated nodes
    node_objects = [tree.search_nodes(name=leaf_name)[0]
                    for leaf_name in annotated_leaves]
    if len(node_objects) < 2:
        raise ValueError(
            "At least two annotated nodes must be found in the tree.")

    lca = tree.get_common_ancestor(*node_objects)

    # Step 3: Expand the LCA subtree to include all explicitly preserved nodes
    expanded_nodes = set(lca.iter_descendants()) | nodes_to_preserve

    # Step 4: Prune based on explicitly preserved nodes
    tree.prune([node.name for node in expanded_nodes if node.name],
               preserve_branch_length=True)

    # Count nodes in the modified tree after pruning
    total_nodes_after_pruning = len(list(tree.traverse()))

    # Step 5: Check if aggressive pruning is needed based on the modified tree size
    if total_nodes_after_pruning > node_threshold:
        tree = collapse_irrelevant_nodes_1(
            tree, nodes_to_preserve)  # Pass only preserved nodes
        total_nodes_after_collapse = len(list(tree.traverse()))
    else:
        print("No aggressive pruning applied")

    # Step 6: Write the modified tree to Newick format
    collapsed_newick = tree.write(format=1)
    return collapsed_newick


def collapse_irrelevant_nodes_1(tree, nodes_to_preserve):
    # Convert preserved nodes to a set for faster lookup
    preserved_names = {n.name for n in nodes_to_preserve}

    for node in tree.traverse("postorder"):
        if node.name not in preserved_names and not node.is_leaf():
            node.delete(prevent_nondicotomic=False)

    # Ensure we prune only those that are not preserved
    tree.prune([n.name for n in nodes_to_preserve if n.name])

    return tree


def create_subtree_and_save(df, selected_rows_indices, tree_file_path, node_threshold=10):
    if not tree_file_path or not os.path.isfile(tree_file_path):
        raise ValueError(
            f"Tree file '{tree_file_path}' is missing or not found.")

    tree = Tree(tree_file_path, format=8)
    total_tree_nodes = len(tree)
    selected_subtree = df.loc[selected_rows_indices]

    if total_tree_nodes <= node_threshold:
        subtree_newick = tree.write(format=1)  # Use format=1 to retain labels
    else:
        if len(selected_subtree) == 1:
            selected_subtree = pd.DataFrame([selected_subtree.iloc[0]])

        
        annotation_str = " -> ".join(f"{row['C_Map_1']} ; {row['C_Map_2']}" for _, row in selected_subtree.iterrows())
        annotations = annotation_str.split(';')

        nodes = []
        for annotation in annotations:
            parts = annotation.split('->')
            if len(parts) > 1:
                nodes.append(parts[1].strip())
        unique_nodes = list(set(nodes))
        st.write(unique_nodes)
        # Remove duplicates and ensure we have at least one node
        if len(unique_nodes) < 1:
            raise ValueError("No valid nodes found in the annotations.")

        # If only one node, extract the subtree for that node
        if len(unique_nodes) == 1:
            subtree = tree & unique_nodes[0]
            # Convert subtree to Newick format string
            # Retain internal node labels
            subtree_newick = subtree.write(format=1)
        else:
            # Separate leaf nodes from the rest
            leaf_nodes = [node for node in unique_nodes if tree.search_nodes(name=node)[
                0].is_leaf()]

            if leaf_nodes:
                # Preserve and collapse nodes for leaf nodes
                nodes_to_preserve = preserve_relevant_nodes(tree, unique_nodes)
                collapsed_tree = collapse_irrelevant_nodes(
                    tree, nodes_to_preserve)

                # Convert the collapsed tree to Newick format
                subtree_newick = collapsed_tree.write(
                    format=1)  # Retain internal node label
            else:
                # Use the new function to preserve and collapse the relevant nodes
                subtree_newick = preserve_nodes_and_find_subtree(
                    tree, unique_nodes)

    # Save the subtree (or entire tree) to a temporary file in Newick format
    temp_subtree_file = tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".nh")
    temp_subtree_file.write(subtree_newick)
    temp_subtree_file.close()

    # Save the pairwise data (selected rows) to a temporary file
    temp_pairwise_file = tempfile.NamedTemporaryFile(
        delete=False, mode="w", newline="")
    selected_subtree.to_csv(temp_pairwise_file.name, index=False)
    temp_pairwise_file.close()

    return temp_subtree_file.name, temp_pairwise_file.name

# Function to inspect the CSV files created by create_subtree_and_save


def inspect_csv_files(subtree_file, pairwise_file):
    # Read the CSV files into DataFrames
    subtree_df = pd.read_csv(subtree_file)
    pairwise_df = pd.read_csv(pairwise_file)


# Track analysis completion status in session state
if 'analysis_completed' not in st.session_state:
    st.session_state.analysis_completed = False

# Upload the tree file
# uploaded_tree_file = st.file_uploader("Upload your tree file", type="nh")
if tree_file is not None:
    # Save to a temporary file and store the path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".nh") as tmp:
        tmp.write(tree_file.getvalue())
        st.session_state.tree_file = tmp.name  # Store path in session state

# Button to proceed to visualization
if st.button('Proceed to Visualize Analysis'):
    if 'tree_file' in st.session_state:
        if 'raw_pairwise_df' in st.session_state:
            st.session_state.raw_df = st.session_state.raw_pairwise_df.copy()
        else:
            st.error("Raw pairwise data not found in session state. Please run the analysis first.")
        st.session_state.analysis_completed = True
    else:
        st.error("Please upload a tree file.")

# Show annotation options only if analysis has been completed
if st.session_state.analysis_completed:
    # Ensure raw_df exists before proceeding
    if 'raw_df' in st.session_state:
        # Place the slider at the top to select the correlation threshold
        correlation_threshold = st.slider("Select correlation threshold", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
        # Save the chosen slider value for later use
        st.session_state.correlation_threshold = correlation_threshold

        # Retrieve the raw dataframe from session state
        raw_df = st.session_state.raw_df.copy()
        
        # Apply the wrangling steps on the raw data:
        # 1. Filter by correlation using the slider value:
        df = raw_df[raw_df['Correlation'] >= correlation_threshold]
        
        # 2. Exclude rows where Transition_2 is "unknown" or where Char_1 and Char_2 contain "BodyLength"
        df = df[
            (df['Transition_2'] != 'unknown') &
            (~df['Char_1'].str.contains('BodyLength')) &
            (~df['Char_2'].str.contains('BodyLength'))
        ]
        
        # 3. Further filter out rows where Transition_1 or Transition_2 contain "unknown"
        df = df[~df['Transition_1'].str.contains('unknown', na=False) &
                ~df['Transition_2'].str.contains('unknown', na=False)]
        
        # 4. Select the relevant columns (including 'Correlation')
        df = df[['Char_1', 'Char_2', 'Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2', 'Correlation']]
        
        # 5. Clean up the text fields for Transition and C_Map columns
        for col in ['Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2']:
            df[col] = df[col].str.replace(' ', '', regex=False)
        
        # 6. Replace 'absent' and 'present' with 0 and 1 for the Transition columns
        df['Transition_1'] = df['Transition_1'].str.replace('absent', '0').str.replace('present', '1')
        df['Transition_2'] = df['Transition_2'].str.replace('absent', '0').str.replace('present', '1')
        
        # 7. Create a new merged index column and set it as the index
        df['Merged_Index'] = df['Char_1'] + " - " + df['Char_2']
        df = df.set_index('Merged_Index')
        
        # Check if the filtered dataframe is empty.
        if df.empty:
            st.error("No pairwise records meet the selected correlation threshold. Please choose a different threshold that exists in your pairwise file.")
        else:
            # Store the filtered, wrangled data in session state
            st.session_state.df = df


    st.write("### Select Row(s) to Annotate")

    # Primary annotation selection
    annotation_1 = st.selectbox(
        "Select Annotation:", options=st.session_state.df.index.unique(), key="annotation_1")

    # Option to add a second annotation
    add_second_annotation = st.checkbox("Include a second annotation")

    # Conditional second annotation selection
    annotation_2 = None
    if add_second_annotation:
        annotation_2 = st.selectbox(
            "Select Second Annotation (optional):",
            options=[opt for opt in st.session_state.df.index.unique()
                     if opt != annotation_1],
            key="annotation_2"
        )

    # Get selected rows for the annotations
    # Always include the first annotation
    selected_rows_indices = [annotation_1]
    if add_second_annotation and annotation_2:  # Only add second annotation if selected
        selected_rows_indices.append(annotation_2)

    # Ensure `selected_rows_indices` contains unique values and no multidimensional structure
    selected_rows_indices = list(set(selected_rows_indices))

    # Ensure `selected_rows_indices` corresponds to actual row indices in the dataframe
    selected_subtree = st.session_state.df.loc[selected_rows_indices]

    # Create and save subtree and pairwise files
    temp_subtree_file, temp_pairwise_file = create_subtree_and_save(
        st.session_state.df, selected_rows_indices, st.session_state.tree_file)

    # Debug print for the subtree and pairwise DataFrame
    st.write("### Pairwise DataFrame (CSV) Content")
    pairwise_df = pd.read_csv(temp_pairwise_file)
    st.write(pairwise_df)  # Display the pairwise DataFrame in the app

    # Print the Newick format of the subtree
    with open(temp_subtree_file, 'r') as f:
        newick_content = f.read()
        st.write("### Subtree (Newick Format) Content")
        st.text(newick_content)  # Display the Newick formatted tree

    # Conditions for visualizations
    # Fetch selected rows for condition checks
    selected_rows = st.session_state.df.loc[selected_rows_indices]
    if annotation_2 and all(selected_rows["C_Map_1"].apply(lambda x: ";" not in x)) and all(selected_rows["C_Map_2"].apply(lambda x: ";" not in x)):
        # Inspect the generated CSV files
        if st.button('Run Visualization 1'):
            # Initialize the progress bar for visualizations
            progress = st.progress(0)  # Set up the progress bar

            st.write("Selected rows for Visualization 1:",
                     selected_rows_indices)
            progress.progress(25)  # Update progress to 25%

            annotation_args = [annotation_1, annotation_2]
            result_viz1 = subprocess.run(
                ["Rscript",
                    "visualization1.1.R",  temp_subtree_file, temp_pairwise_file],
                capture_output=True
            )
            progress.progress(75)  # Update progress to 50%
            if result_viz1.returncode == 0:
                st.success("Visualization 1 completed!")
                progress.progress(100)  # Update progress to 100%

                image = Image.open("images/viz1.png")
                st.image(
                    image, caption="Visualization 1 with Annotations", width=1000)
            else:
                st.error("Error in Visualization 1.")
                st.write(result_viz1.stderr.decode())

    elif not annotation_2 and (any(selected_rows["C_Map_1"].str.contains(";")) or any(selected_rows["C_Map_2"].str.contains(";"))):
        # When running Visualization 2
        if st.button('Run Visualization 2'):
            # Initialize the progress bar for visualizations
            progress = st.progress(0)  # Set up the progress bar
            st.write("Selected rows for Visualization 2:",
                     selected_rows_indices)
            progress.progress(25)  # Update progress to 25%

            # Run the R script for Visualization 2
            result_viz2 = subprocess.run(
                ["Rscript",  # Path to Rscript
                 # Path to the R script
                 "visualization2.R",
                 temp_subtree_file,  # Path to the subtree Newick file
                 temp_pairwise_file],  # Pass the CSV file path to R script
                capture_output=True
            )
            progress.progress(75)  # Update progress to 50%

            if result_viz2.returncode == 0:
                st.success("Visualization 2 completed!")
                progress.progress(100)  # Update progress to 100%

                # Assuming the R script generates a plot as 'viz2.png'
                image = Image.open("images/viz2.png")
                st.image(
                    image, caption="Visualization 2 with Annotations", width=1000)
            else:
                st.error("Error in Visualization 2.")
                st.write(result_viz2.stderr.decode())