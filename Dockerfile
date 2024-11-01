# Use a base image that includes R
FROM rocker:4.4.1  # Change the R version as needed

# Set the working directory
WORKDIR /app

# Copy your project files
COPY . .

# Install R packages
COPY install.R /app/install.R
RUN Rscript /app/install.R

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install -r requirements.txt

# Command to run the Streamlit application
CMD ["streamlit", "run", "Home.py"]
