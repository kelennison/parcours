# Use a base image that includes Python
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install R and necessary packages
RUN apt-get update && \
    apt-get install -y r-base && \
    apt-get clean

# Copy your project files
COPY . .

# Install R packages
RUN Rscript install.R

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Streamlit application
CMD ["streamlit", "run", "Home.py"]
