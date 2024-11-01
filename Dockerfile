# Use a base image that includes both R and Python
FROM rocker/r-ver:4.2.2  # Use the desired R version

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    python3 \
    python3-pip \
    && apt-get clean

# Copy your requirements and install Python packages
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

# Copy the R package installation script and run it
COPY install.R /app/
RUN Rscript /app/install.R

# Set the working directory
WORKDIR /app

# Copy the rest of your application code
COPY . /app/

# Command to run your Streamlit app
CMD ["streamlit", "run", "Home.py"]
