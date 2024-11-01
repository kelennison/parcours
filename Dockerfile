# Use a base image with Python
FROM python:3.10-slim

# Install R and required system libraries
RUN apt-get update && apt-get install -y \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Use the latest version of the Bioconductor image with ggtree
docker pull quay.io/biocontainers/bioconductor-ggtree:<tag> [1]

# Install additional R packages
RUN R -e "install.packages(c('ape', 'tidyverse'), repos='https://cloud.r-project.org')"


# Install Python packages from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Set the command to run your Streamlit app
CMD ["streamlit", "run", "Home.py"]
