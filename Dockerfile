# Start with a Python base image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add the CRAN GPG key
RUN wget -qO- https://cloud.r-project.org/bin/linux/debian/marutter.gpg | apt-key add -

# Add the CRAN repository for R
RUN echo "deb https://cloud.r-project.org/bin/linux/debian bullseye-cran40/" > /etc/apt/sources.list.d/r.list

# Update package lists and install R
RUN apt-get update && apt-get install -y \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the Rscript path explicitly
ENV PATH="/usr/lib/R/bin:${PATH}"

# Verify R installation
RUN Rscript --version

# Install Bioconductor and necessary CRAN packages
RUN R -e "install.packages('BiocManager', repos='https://cloud.r-project.org')" \
    && R -e "BiocManager::install('ggtree')" \
    && R -e "install.packages(c('ape', 'tidyverse'), repos='https://cloud.r-project.org')"

# Copy and install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]
