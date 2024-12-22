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


# Page setup
st.set_page_config(layout="wide")
st.title('Parcours: Correlated Evolution Analysis')

# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")  # Load your existing CSS file

# File upload widgets for required files
st.write('Upload your phylogenetic tree, character state data, and config file:')
config_file = st.file_uploader("Choose config file for the analysis", type=["csv"])
extant_file = st.file_uploader("Choose extant state file", type=["csv"])
tree_file = st.file_uploader("Choose phylogenetic tree file", type=["nh", "tree"])

# Save config and tree files to temporary files and store paths in session state
if config_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(config_file.getvalue())
        st.session_state.config_file_path = tmp.name  # Store path in session state

if tree_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".nh") as tmp:
        tmp.write(tree_file.getvalue())
        st.session_state.tree_file_path = tmp.name  # Store path in session state

# Initialize optional files
cost_file = None
physical_file = None

# Function to check if specific files are referenced in the config file


def check_file_in_config(file_path, keyword):
    if file_path:
        config_data = pd.read_csv(file_path)
        # Flatten data to check for the presence of keywords
        if keyword in config_data.to_string().lower():
            return True
    return False


# Automatically set optional files based on config file content
if config_file:
    if check_file_in_config(st.session_state.config_file_path, 'cost.csv'):
        st.write(
            "Cost file is mentioned in the config file, automatically adding it to the list.")
        cost_file = st.file_uploader("Upload cost file", type=["csv"])
    if check_file_in_config(st.session_state.config_file_path, 'physical.csv'):
        st.write(
            "Physical trait file is mentioned in the config file, automatically adding it to the list.")
        physical_file = st.file_uploader(
            "Upload physical trait file", type=["csv"])

# Set the Python interpreter path
python_path = sys.executable

# Function to clear output files
def clear_output_files():
    files_to_remove = glob.glob("*.csv") + glob.glob("*.nexus") + glob.glob("solutions/*")
    for file_path in files_to_remove:
        os.remove(file_path)

# Button to run analysis with a spinner
if st.button('Run Analysis'):
    # Ensure all required files are present
    if extant_file and tree_file and config_file:
        # Clear previous output files
        clear_output_files()

        # Save required files
        with open("config.csv", "wb") as f:
            f.write(config_file.getbuffer())
        with open("extant.csv", "wb") as f:
            f.write(extant_file.getbuffer())
        with open("tree.nh", "wb") as f:
            f.write(tree_file.getbuffer())

        # Save optional files if uploaded
        if cost_file:
            with open("cost.csv", "wb") as f:
                f.write(cost_file.getbuffer())
        if physical_file:
            with open("physical.csv", "wb") as f:
                f.write(physical_file.getbuffer())

        # Define paths
        parcours_script = r"parcours.py"
        config_file_path = "config.csv"

        # Define the command to run the Python script with all required arguments
        command = [python_path, parcours_script, "-f", config_file_path, "-t", "tree.nh", "-e", "extant.csv"]

        # Add cost and physical files to the command with separate flags
        if cost_file:
            command += ["-c", "cost.csv"]
        if physical_file:
            command += ["-p", "pairwise.csv"]

        # Run analysis with spinner
        with st.spinner("Running analysis..."):
            result = subprocess.run(command, capture_output=True, text=True)

        # Display results
        if result.returncode == 0:
            st.success("Analysis completed successfully!")
            st.write(result.stdout)

            # Collect output files and check existence before adding them to the ZIP
            output_files = ["output.csv", "pairwise.csv", "unit.csv", "solns.csv"]
            output_dir = "solutions"
            output_files.extend([os.path.join(output_dir, f) for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))])

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

# Visualization button
if st.button('Run Visualization'):
    # Print current working directory for debugging
    st.write("Current Working Directory:", os.getcwd())

    # Initialize the progress bar for visualizations
    progress = st.progress(0)  # Set up the progress bar

    # Run visualization1.R with subprocess.Popen
    progress.progress(25)  # Update progress to 25%
    process_viz1 = subprocess.Popen(["Rscript", "visualization1.R"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout_viz1, stderr_viz1 = process_viz1.communicate()

    # Check if visualization1.R completed successfully
    if process_viz1.returncode == 0:
        st.success("Visualization 1 completed!")
        progress.progress(50)  # Update progress to 50%
        try:
            # Load the generated image
            image = Image.open("images/viz1.png")
            st.image(image, caption="Visualization 1", width=1000)
        except FileNotFoundError:
            st.error("Visualization 1 completed, but viz1.png not found.")
    else:
        st.error("Error in Visualization 1.")
        st.write(stderr_viz1)

    # Run visualization2.R with subprocess.Popen
    progress.progress(75)  # Update progress to 75%
    process_viz2 = subprocess.Popen(["Rscript", "visualization2.R"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout_viz2, stderr_viz2 = process_viz2.communicate()

    # Check if visualization2.R completed successfully
    if process_viz2.returncode == 0:
        st.success("Visualization 2 completed!")
        progress.progress(100)  # Update progress to 100%
        try:
            # Load the generated image
            image = Image.open("images/viz2.png")
            st.image(image, caption="Visualization 2", width=1000)
        except FileNotFoundError:
            st.error("Visualization 2 completed, but viz2.png not found.")
    else:
        st.error("Error in Visualization 2.")
        st.write(stderr_viz2)
