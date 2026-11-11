from ete3 import Tree
import streamlit as st
import subprocess
import sys
import os
import zipfile
import pandas as pd
import glob
from PIL import Image
import tempfile
import shutil
from Bio import Phylo
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
import textwrap  # Add this to your imports at the top of app8.py
import plotly.colors as pc


# Use local CSS (from Home.py)
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def _split_cmap(value):
    """Return annotation destinations from a semicolon-separated C_Map value."""
    if pd.isna(value):
        return []
    destinations = []
    for mapping in str(value).split(";"):
        mapping = mapping.strip()
        if not mapping:
            continue
        destinations.append(mapping.split("->", 1)[-1].strip())
    return destinations


def _format_node_label(node_name):
    """Make node-to-node mappings easier to read in heatmap row labels."""
    if node_name is None:
        return ""
    node_name = str(node_name).strip()
    return node_name.replace("->", " → ")


def get_distinct_colors(n):
    """Generate a list of highly distinct colors for the transitions."""
    palettes = [
        pc.qualitative.Plotly,
        pc.qualitative.D3,
        pc.qualitative.Alphabet,
        pc.qualitative.Dark24,
        pc.qualitative.Light24
    ]
    all_colors = []
    for p in palettes:
        all_colors.extend(p)
    return all_colors[:n]

def hex_to_rgba(hex_color, alpha):
    """Convert a hex color to an rgba string for transparent gradients."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def create_transition_heatmap(selected_df, subtree_file_path, character_filter="Both",
                              min_occurrence=1, show_counts=True,
                              use_log_scale=True):
    """Build the Node × Transition heatmap with distinct colors mapped to transitions."""
    n_annotations = min(len(selected_df), 4)
    
    # We will track the specific character names (e.g., "A.Gestation") per column
    cell_counts = defaultdict(int)
    cell_char_names = defaultdict(set)
    col_char_names = defaultdict(set)

    for annotation_index, (_, row) in enumerate(selected_df.iterrows()):
        if annotation_index >= 4:
            break
            
        # 1. Character 1 maps STRICTLY to Transition 1, C_Map 1, and Char_1
        if character_filter in ("Both", "Character 1"):
            trans = str(row["Transition_1"]).strip()
            char_name = str(row["Char_1"]).strip()
            key = ("Char 1", trans)
            col_char_names[key].add(char_name)
            for node in _split_cmap(row["C_Map_1"]):
                cell_counts[(node, key)] += 1
                cell_char_names[(node, key)].add(char_name)
                
        # 2. Character 2 maps STRICTLY to Transition 2, C_Map 2, and Char_2
        if character_filter in ("Both", "Character 2"):
            trans = str(row["Transition_2"]).strip()
            char_name = str(row["Char_2"]).strip()
            key = ("Char 2", trans)
            col_char_names[key].add(char_name)
            for node in _split_cmap(row["C_Map_2"]):
                cell_counts[(node, key)] += 1
                cell_char_names[(node, key)].add(char_name)

    if not cell_counts:
        return None

    try:
        subtree = Tree(subtree_file_path, format=1)
        tree_order = [node.name for node in subtree.traverse("preorder") if node.name]
    except Exception:
        tree_order = []

    observed_nodes = {node for node, _ in cell_counts}
    ordered_nodes = [node for node in tree_order if node in observed_nodes]
    ordered_nodes.extend(sorted(observed_nodes - set(ordered_nodes)))
    
    # Get unique columns (e.g., ("Char 1", "4->3") and ("Char 2", "4->3"))
    ordered_columns = sorted({col_key for _, col_key in cell_counts})
    
    # Create clean x-axis labels (bottom of the heatmap)
    x_labels = []
    for char_type, trans in ordered_columns:
        if character_filter == "Both":
            x_labels.append(f"{trans} ({char_type})")
        else:
            x_labels.append(trans)

    counts = np.zeros((len(ordered_nodes), len(ordered_columns)), dtype=int)
    hover_texts = np.full((len(ordered_nodes), len(ordered_columns)), "", dtype=object)

    for r_idx, node in enumerate(ordered_nodes):
        for c_idx, col_key in enumerate(ordered_columns):
            val = cell_counts.get((node, col_key), 0)
            if val >= min_occurrence:
                counts[r_idx, c_idx] = val
                char_names = sorted(cell_char_names.get((node, col_key), []))
                # Just list the character name(s), no ": count" appended
                hover_texts[r_idx, c_idx] = ", ".join(char_names)

    distinct_colors = get_distinct_colors(len(ordered_columns))

    traces = [
        go.Heatmap(
            z=np.zeros_like(counts),
            x=x_labels, y=ordered_nodes,
            colorscale=[[0, "#e8e8e8"], [1, "#e8e8e8"]],
            showscale=False, xgap=1, ygap=1, hoverinfo="skip", name="Base"
        )
    ]

    for j, col_key in enumerate(ordered_columns):
        char_type, trans = col_key
        col_data = counts[:, j]
        max_val = max(1, int(col_data.max()))
        
        z = np.full_like(counts, np.nan, dtype=float)
        z[:, j] = np.where(col_data > 0, col_data, np.nan)
        
        zmin_val = 0.0
        if use_log_scale:
            z[:, j] = np.log1p(z[:, j])
            zmax_val = float(np.log1p(max_val))
        else:
            zmax_val = float(max_val)
            
        text = np.full(counts.shape, "", dtype=object)
        if show_counts:
            text[:, j] = [str(int(c)) if c > 0 else "0" for c in col_data]

        if max_val > 1:
            tickvals = [zmin_val, zmax_val]
            ticktext = ["0", str(max_val)]
        else:
            tickvals = [zmin_val]
            ticktext = ["0"]

        base_color = distinct_colors[j]
        light_color = hex_to_rgba(base_color, 0.05)
        
        # Build the legend title using the specific character name(s)
        col_chars = sorted(col_char_names.get(col_key, []))
        char_title = f"<b>{', '.join(col_chars)}</b>"
        if character_filter == "Both":
            # If they share the same transition, make it clear which Char is which
            char_title = f"<b>{char_type}: {', '.join(col_chars)}</b>"
        
        # Character on top, Transition underneath
        legend_title = f"{char_title}<br><span style='font-size:10px;color:#555'>Transition {trans}</span>"

        traces.append(go.Heatmap(
            z=z, x=x_labels, y=ordered_nodes,
            text=text, texttemplate="%{text}", textfont=dict(color="#111111"),
            customdata=hover_texts,
            colorscale=[[0, light_color], [1, base_color]],
            zmin=zmin_val, zmax=zmax_val,
            xgap=1, ygap=1, hoverongaps=False,
            hovertemplate=(
                "<b>Character:</b> %{customdata}<br>"
                f"<b>Transition:</b> {trans}<br>"
                "<b>Node:</b> %{y}<br>"
                "<b>Count:</b> %{text}<br>"
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=dict(
                    text=legend_title, 
                    side="top",
                    font=dict(color="#111111", size=11)
                ), 
                x=1.02, thickness=14,
                tickfont=dict(color="#111111", size=11),
                tickmode="array", 
                tickvals=tickvals, ticktext=ticktext,
                outlinewidth=0,
            ),
        ))

    # --- SPACING FIX: Make colorbars much longer ---
    n_transitions = len(ordered_columns)
    for i, trace in enumerate(traces[1:]):
        slot_height = 1.0 / n_transitions
        cb_len = slot_height * 0.80 
        y_top = 1.0 - (i * slot_height)
        y_center = y_top - (slot_height / 2) - 0.02
        
        trace.colorbar.y = y_center
        trace.colorbar.len = cb_len

    figure = go.Figure(traces)
    figure.update_layout(
        template="plotly_white",
        title=dict(
            text="Node × Transition heatmap",
            font=dict(color="#111111", size=15),
            x=0.02, xanchor="left"
        ),
        xaxis=dict(
            title=dict(text="Transition (State → State)", font=dict(color="#111111")), 
            showgrid=False,
            tickfont=dict(color="#111111")
        ),
        yaxis=dict(
            title=dict(text="Node / evolutionary position", font=dict(color="#111111")),
            autorange="reversed",
            tickmode="array", tickvals=ordered_nodes,
            ticktext=[_format_node_label(node) for node in ordered_nodes],
            showgrid=False,
            tickfont=dict(color="#111111")
        ),
        plot_bgcolor="white", 
        paper_bgcolor="white",
        height=max(800, 45 * len(ordered_nodes) + 350),
        margin=dict(l=280, r=280, t=90, b=90), 
        showlegend=False,
    )
    return figure

def wrangle_pairwise_data(tree_path):
    pairwise_path = "pairwise.csv"
    if os.path.exists(pairwise_path):
        df = pd.read_csv(pairwise_path)
        df = df[
            (df['Transition_2'] != 'unknown') &
            (~df['Char_1'].str.contains('BodyLength')) &
            (~df['Char_2'].str.contains('BodyLength'))
        ]
        df = df[~df['Transition_1'].str.contains('unknown', na=False) &
                ~df['Transition_2'].str.contains('unknown', na=False)]
        df = df[['Char_1', 'Char_2', 'Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2']]
        for col in ['Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2']:
            df[col] = df[col].str.replace(' ', '', regex=False)
        df['Transition_1'] = df['Transition_1'].str.replace('absent', '0').str.replace('present', '1')
        df['Transition_2'] = df['Transition_2'].str.replace('absent', '0').str.replace('present', '1')
        df['Merged_Index'] = df['Char_1'] + " - " + df['Char_2']
        df = df.set_index('Merged_Index')
        wrangled_pairwise_path = "wrangled_pairwise.csv"
        df.to_csv(wrangled_pairwise_path, index=False)
        return df, wrangled_pairwise_path, "subtree_output_path"
    return None, None, None

def convert_tree_to_nh(uploaded_file):
    filename = uploaded_file.name.lower()
    suffix = os.path.splitext(filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        input_path = tmp.name

    try:
        if suffix in [".nex", ".nexus"]:
            tree = Phylo.read(input_path, "nexus")
            leaf_names = set()
            for clade in tree.find_clades():
                if not clade.clades:
                    if clade.name:
                        leaf_names.add(str(clade.name))
            internal_counter = 1
            for clade in tree.find_clades():
                clade.branch_length = None
                if clade.clades:
                    existing_name = str(clade.name).strip() if clade.name is not None else ""
                    if existing_name:
                        clade.name = existing_name
                    else:
                        while True:
                            new_name = str(internal_counter)
                            internal_counter += 1
                            if new_name not in leaf_names:
                                break
                        clade.name = new_name
                else:
                    if clade.name is None:
                        raise ValueError("The NEXUS tree contains a leaf with no name.")
                    clade.name = str(clade.name).replace(r"\_", "_").strip()
            from io import StringIO
            handle = StringIO()
            Phylo.write(tree, handle, "newick")
            newick = handle.getvalue()
            newick = newick.replace(r"\_", "_")
            import re
            newick = re.sub(r":[0-9eE.+-]+", "", newick)
            newick = re.sub(r"\s+", " ", newick).strip()
            ete_tree = Tree(newick, format=8)
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".nh").name
            ete_tree.write(outfile=output_path, format=8)
            return output_path
        elif suffix in [".nh", ".tree"]:
            tree = Tree(input_path, format=8)
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".nh").name
            tree.write(outfile=output_path, format=8)
            return output_path
        else:
            raise ValueError(f"Unsupported tree format: {suffix}")
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        raise ValueError(f"Could not process the tree file: {e}")

# Page setup
st.set_page_config(layout="wide")
st.title('Parcours: Correlated Evolution Analysis')

# Load CSS
local_css("style/style.css")

# --- File upload widgets ---
st.write('Upload your phylogenetic tree and character state data:')
extant_file = st.file_uploader("Choose extant state file", type=["csv"])
tree_file = st.file_uploader(
    "Upload phylogenetic tree",
    type=["nh", "tree", "nex", "nexus"],
    help="Supported formats: Newick (.nh, .tree) and NEXUS (.nex, .nexus). NEXUS files are automatically converted to Newick format before analysis."
)

# Relative paths for GitHub
config_file_path = os.path.join("assets", "config1.csv")
fixed_physical_file_path = os.path.join("assets", "physical.csv")

st.session_state["config_file_path"] = config_file_path

if tree_file is not None:
    try:
        converted_tree_path = convert_tree_to_nh(tree_file)
        st.session_state.tree_file_path = converted_tree_path
        if tree_file.name.lower().endswith((".nex", ".nexus")):
            st.success(f"NEXUS file '{tree_file.name}' converted to Newick format successfully.")
        else:
            st.success(f"Tree file '{tree_file.name}' loaded successfully.")
    except Exception as e:
        st.error(str(e))
        st.stop()

cost_file = None

def check_file_in_config(file_path, keyword):
    if file_path and os.path.exists(file_path):
        config_data = pd.read_csv(file_path)
        if keyword.lower() in config_data.to_string().lower():
            return True
    return False

if os.path.exists(config_file_path):
    if check_file_in_config(config_file_path, 'cost.csv'):
        st.write("Cost file is mentioned in the config file, automatically adding it to the list.")
        cost_file = st.file_uploader("Upload cost file", type=["csv"])

python_path = sys.executable

def clear_output_files():
    files_to_remove = glob.glob("*.csv") + glob.glob("*.nexus") + glob.glob("solutions/*")
    for file_path in files_to_remove:
        os.remove(file_path)

analysis_completed = False
wrangled_pairwise_path = None

if st.button('Run Analysis'):
    if extant_file and tree_file:
        clear_output_files()

        with open("extant.csv", "wb") as f:
            f.write(extant_file.getbuffer())
        
        if tree_file:
            try:
                converted_tree_path = convert_tree_to_nh(tree_file)
                shutil.copy(converted_tree_path, "tree.nh")
                st.session_state.tree_file_path = converted_tree_path
            except Exception as e:
                st.error(f"Unable to process tree file: {e}")
                st.stop()

        if cost_file:
            with open("cost.csv", "wb") as f:
                f.write(cost_file.getbuffer())

        if not os.path.exists(config_file_path):
            st.error(f"Config file not found at: {config_file_path}")
        elif not os.path.exists(fixed_physical_file_path):
            st.error(f"Physical file not found at: {fixed_physical_file_path}")
        else:
            shutil.copy(fixed_physical_file_path, "physical.csv")
            
            parcours_script = "parcours.py"
            command = [python_path, parcours_script,
                       "-f", config_file_path,
                       "-t", "tree.nh",
                       "-e", "extant.csv"]

            if cost_file:
                command += ["-c", "cost.csv"]

            command += ["-p", "pairwise.csv"]

            with st.spinner("Running analysis..."):
                result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0:
                st.success("Analysis completed successfully!")
                st.write(result.stdout)

                if os.path.exists("pairwise.csv"):
                    raw_df = pd.read_csv("pairwise.csv")
                    st.session_state.raw_pairwise_df = raw_df
                else:
                    st.error("pairwise.csv not found!")

                df, wrangled_pairwise_path, subtree_path = wrangle_pairwise_data("tree.nh")
                analysis_completed = True

                output_files = ["output.csv", "pairwise.csv", "unit.csv", "solns.csv"]
                output_dir = "solutions"
                if os.path.exists(output_dir):
                    output_files.extend([os.path.join(output_dir, f) for f in os.listdir(output_dir)
                                         if os.path.isfile(os.path.join(output_dir, f))])
                if wrangled_pairwise_path:
                    output_files.append(wrangled_pairwise_path)

                zip_path = "analysis_results.zip"
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file in output_files:
                        if os.path.exists(file):
                            zipf.write(file)

                with open(zip_path, "rb") as f:
                    with st.spinner("Preparing download..."):
                        st.download_button(
                            label="Download Analysis Results",
                            data=f,
                            file_name=zip_path,
                            mime="application/zip")
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
        target_node = tree.search_nodes(name=leaf_name)[0]
        nodes_to_preserve.add(target_node)
        current_node = target_node.up
        while current_node:
            nodes_to_preserve.add(current_node)
            for sibling in current_node.children:
                nodes_to_preserve.add(sibling)
            current_node = current_node.up
    return nodes_to_preserve

def collapse_irrelevant_nodes(tree, nodes_to_preserve):
    for node in tree.traverse("postorder"):
        if node not in nodes_to_preserve and not node.is_leaf():
            node.delete(prevent_nondicotomic=False)
    tree.prune([n.name for n in nodes_to_preserve if n.name])
    return tree

def preserve_nodes_and_find_subtree(tree, annotated_leaves, node_threshold=30):
    nodes_to_preserve = set()
    for leaf_name in annotated_leaves:
        target_node = tree.search_nodes(name=leaf_name)[0]
        nodes_to_preserve.add(target_node)
        current_node = target_node.up
        while current_node:
            nodes_to_preserve.add(current_node)
            nodes_to_preserve.update(current_node.children)
            current_node = current_node.up

    node_objects = [tree.search_nodes(name=leaf_name)[0] for leaf_name in annotated_leaves]
    if len(node_objects) < 2:
        raise ValueError("At least two annotated nodes must be found in the tree.")

    lca = tree.get_common_ancestor(*node_objects)
    expanded_nodes = set(lca.iter_descendants()) | nodes_to_preserve
    tree.prune([node.name for node in expanded_nodes if node.name], preserve_branch_length=True)

    total_nodes_after_pruning = len(list(tree.traverse()))
    if total_nodes_after_pruning > node_threshold:
        tree = collapse_irrelevant_nodes_1(tree, nodes_to_preserve)
    collapsed_newick = tree.write(format=1)
    return collapsed_newick

def collapse_irrelevant_nodes_1(tree, nodes_to_preserve):
    preserved_names = {n.name for n in nodes_to_preserve}
    for node in tree.traverse("postorder"):
        if node.name not in preserved_names and not node.is_leaf():
            node.delete(prevent_nondicotomic=False)
    tree.prune([n.name for n in nodes_to_preserve if n.name])
    return tree

def create_subtree_and_save(df, selected_rows_indices, tree_file_path, node_threshold=10):
    if not tree_file_path or not os.path.isfile(tree_file_path):
        raise ValueError(f"Tree file '{tree_file_path}' is missing or not found.")

    tree = Tree(tree_file_path, format=8)
    total_tree_nodes = len(tree)
    selected_subtree = df.loc[selected_rows_indices]

    if total_tree_nodes <= node_threshold:
        subtree_newick = tree.write(format=1)
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
        if len(unique_nodes) < 1:
            raise ValueError("No valid nodes found in the annotations.")

        if len(unique_nodes) == 1:
            subtree = tree & unique_nodes[0]
            subtree_newick = subtree.write(format=1)
        else:
            leaf_nodes = [node for node in unique_nodes if tree.search_nodes(name=node)[0].is_leaf()]
            if leaf_nodes:
                nodes_to_preserve = preserve_relevant_nodes(tree, unique_nodes)
                collapsed_tree = collapse_irrelevant_nodes(tree, nodes_to_preserve)
                subtree_newick = collapsed_tree.write(format=1)
            else:
                subtree_newick = preserve_nodes_and_find_subtree(tree, unique_nodes)

    temp_subtree_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".nh")
    temp_subtree_file.write(subtree_newick)
    temp_subtree_file.close()

    temp_pairwise_file = tempfile.NamedTemporaryFile(delete=False, mode="w", newline="")
    selected_subtree.to_csv(temp_pairwise_file.name, index=False)
    temp_pairwise_file.close()

    return temp_subtree_file.name, temp_pairwise_file.name

if 'analysis_completed' not in st.session_state:
    st.session_state.analysis_completed = False

if st.button('Proceed to Visualize Analysis'):
    if 'tree_file_path' in st.session_state:
        if 'raw_pairwise_df' in st.session_state:
            st.session_state.raw_df = st.session_state.raw_pairwise_df.copy()
        else:
            st.error("Raw pairwise data not found in session state. Please run the analysis first.")
        st.session_state.analysis_completed = True
    else:
        st.error("Please upload a tree file.")

if st.session_state.analysis_completed:
    if 'raw_df' in st.session_state:
        correlation_threshold = st.slider("Select correlation threshold", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
        st.session_state.correlation_threshold = correlation_threshold

        raw_df = st.session_state.raw_df.copy()
        
        df = raw_df[raw_df['Correlation'] >= correlation_threshold]
        df = df[
            (df['Transition_2'] != 'unknown') &
            (~df['Char_1'].str.contains('BodyLength')) &
            (~df['Char_2'].str.contains('BodyLength'))
        ]
        df = df[~df['Transition_1'].str.contains('unknown', na=False) &
                ~df['Transition_2'].str.contains('unknown', na=False)]
        df = df[['Char_1', 'Char_2', 'Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2', 'Correlation']]
        
        for col in ['Transition_1', 'Transition_2', 'C_Map_1', 'C_Map_2']:
            df[col] = df[col].str.replace(' ', '', regex=False)
        
        df['Transition_1'] = df['Transition_1'].str.replace('absent', '0').str.replace('present', '1')
        df['Transition_2'] = df['Transition_2'].str.replace('absent', '0').str.replace('present', '1')
        
        df['Merged_Index'] = df['Char_1'] + " - " + df['Char_2']
        df = df.set_index('Merged_Index')
        
        if df.empty:
            st.error("No pairwise records meet the selected correlation threshold. Please choose a different threshold that exists in your pairwise file.")
        else:
            st.session_state.df = df

    st.write("### Select Row(s) to Annotate")

    options = st.session_state.df.index.unique().tolist()
    if not options or options == [None]:
        st.error("No valid annotations available. Please adjust your correlation threshold.")
    else:
        annotation_1 = st.selectbox(
            "Select Annotation:",
            options=options,
            key="annotation_1"
        )

    add_second_annotation = st.checkbox("Include a second annotation")

    annotation_2 = None
    if add_second_annotation:
        annotation_2 = st.selectbox(
            "Select Second Annotation (optional):",
            options=[opt for opt in st.session_state.df.index.unique()
                     if opt != annotation_1],
            key="annotation_2"
        )

    selected_rows_indices = [annotation_1]
    if add_second_annotation and annotation_2:
        selected_rows_indices.append(annotation_2)

    selected_rows_indices = list(set(selected_rows_indices))

    selected_subtree = st.session_state.df.loc[selected_rows_indices]

    temp_subtree_file, temp_pairwise_file = create_subtree_and_save(
        st.session_state.df,
        selected_rows_indices,
        st.session_state.tree_file_path
    )

    st.write("### Pairwise DataFrame (CSV) Content")
    pairwise_df = pd.read_csv(temp_pairwise_file)
    st.write(pairwise_df)

    with open(temp_subtree_file, 'r') as f:
        newick_content = f.read()
        st.write("### Subtree (Newick Format) Content")
        st.text(newick_content)

    selected_rows = st.session_state.df.loc[selected_rows_indices]

    # Route by NUMBER OF SELECTED ROWS (Fixed logic from app7)
    if len(selected_rows) == 1:
        if st.button('Run Visualization 1'):
            progress = st.progress(0)
            st.write("Selected rows for Visualization 1:", selected_rows_indices)
            progress.progress(25)

            result_viz1 = subprocess.run(
                ["Rscript", "visualization1.1.R", temp_subtree_file, temp_pairwise_file],
                capture_output=True
            )
            progress.progress(75)

            if result_viz1.returncode == 0:
                st.success("Visualization 1 completed!")
                progress.progress(100)
                image = Image.open("images/viz1.png")
                st.image(image, caption="Visualization 1 with Annotations", width=1000)
            else:
                st.error("Error in Visualization 1.")
                if result_viz1.stdout:
                    st.write("### R Output")
                    st.code(result_viz1.stdout.decode(), language="text")
                if result_viz1.stderr:
                    st.write("### R Error")
                    st.code(result_viz1.stderr.decode(), language="text")
    else:
        if st.button('Run Visualization 2'):
            progress = st.progress(0)
            st.write("Selected rows for Visualization 2:", selected_rows_indices)
            progress.progress(25)

            result_viz2 = subprocess.run(
                ["Rscript", "visualization2.1.R", temp_subtree_file, temp_pairwise_file],
                capture_output=True
            )
            progress.progress(75)

            if result_viz2.returncode == 0:
                st.success("Visualization 2 completed!")
                progress.progress(100)
                if result_viz2.stdout:
                    st.write("### R Debug Output")
                    st.code(result_viz2.stdout.decode(), language="text")
                image = Image.open("images/viz2.png")
                st.image(image, caption="Visualization 2 with Annotations", width=1000)
            else:
                st.error("Error in Visualization 2.")
                if result_viz2.stdout:
                    st.write("### R Output")
                    st.code(result_viz2.stdout.decode(), language="text")
                if result_viz2.stderr:
                    st.write("### R Error")
                    st.code(result_viz2.stderr.decode(), language="text")

    # Heatmap section (From app7)
    st.divider()
    st.write("### Transition Heatmap (Node × Transition)")

    # Display exactly what is being plotted (Answers Soyong's question)
    char_names = ", ".join([f"**{name}**" for name in selected_rows.index])
    st.info(
        f"**Characters analyzed:** {char_names}\n\n"
        "**How to read this:** Each cell represents the number of times a specific transition "
        "(e.g., state 4 → 2) occurred for the associated character at that evolutionary node."
    )

    heatmap_col_1, heatmap_col_2, heatmap_col_3 = st.columns(3)
    
    with heatmap_col_1:
        heatmap_character_filter = st.radio(
            "Character", ["Both", "Character 1", "Character 2"],
            key="heatmap_character_filter",
        )
        
    with heatmap_col_2:
        heatmap_min_occurrence = st.number_input(
            "Minimum occurrence", min_value=1, value=1, step=1,
            key="heatmap_min_occurrence",
        )
        
    with heatmap_col_3:
        heatmap_show_counts = st.checkbox(
            "Show counts", value=True, key="heatmap_show_counts",
        )
        
    heatmap_use_log = st.checkbox(
        "Use log-scaled intensity", value=True, key="heatmap_use_log",
        help="Compresses high counts while keeping lower counts visible.",
    )

    if st.button("Show Heatmap", key="show_transition_heatmap"):
        heatmap_figure = create_transition_heatmap(
            selected_df=selected_rows,
            subtree_file_path=temp_subtree_file,
            character_filter=heatmap_character_filter,
            min_occurrence=int(heatmap_min_occurrence),
            show_counts=heatmap_show_counts,
            use_log_scale=heatmap_use_log,
        )
        
        if heatmap_figure is None:
            st.warning("No heatmap data matches the current filters.")
        else:
            st.plotly_chart(heatmap_figure, use_container_width=True)