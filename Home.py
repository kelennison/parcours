import streamlit as st
import subprocess
import sys
import os
import zipfile
import pandas as pd
from PIL import Image


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

# Dropdown for selecting optional files to upload
optional_files = st.multiselect(
    "Select optional files to upload (not required for analysis):",
    options=["Cost File", "Physical Trait File"]
)

# Display the appropriate upload fields based on selection
cost_file = None
physical_file = None

if "Cost File" in optional_files:
    cost_file = st.file_uploader("Upload cost file", type=["csv"])
if "Physical Trait File" in optional_files:
    physical_file = st.file_uploader("Upload physical trait file", type=["csv"])

# Set the Python interpreter path
python_path = sys.executable

# Function to clear output files
def clear_output_files():
    files_to_remove = glob.glob("*.csv") + glob.glob("*.nexus") + glob.glob("solutions/*")
    for file_path in files_to_remove:
        os.remove(file_path)

# Button to run analysis
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

        # Run the Python script using subprocess
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

            # Provide a download button for the zip file
            with open(zip_path, "rb") as f:
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

# Visualization 1 button (first R script)
if st.button('Run Visualization'):
    # Print current working directory for debugging
    st.write("Current Working Directory:", os.getcwd())

    result_viz1 = subprocess.run(["Rscript", "visualization1.R"], capture_output=True, text=True)
    if result_viz1.returncode == 0:
        st.success("Visualization 1 completed!")
        image = Image.open("viz1.png")  # Load the generated image
        st.image(image, caption="Visualization 1", width=1000)
    else:
        st.error("Error in Visualization 1.")
        st.write(result_viz1.stderr)

    
    result_viz2 = subprocess.run(["Rscript", "visualization2.R"], capture_output=True, text=True)
    if result_viz2.returncode == 0:
        st.success("Visualization 2 completed!")
        image = Image.open("viz2.png")  # Load the generated image
        st.image(image, caption="Visualization 2", width=1000)
    else:
        st.error("Error in Visualization 2.")
        st.write(result_viz2.stderr)


   

 
