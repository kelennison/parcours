# Use a base image with Python
FROM python:3.10-slim

# Install R 4.4 and required system libraries
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys '51716619E084DAB9' && \
    add-apt-repository 'deb https://cloud.r-project.org/bin/linux/debian bullseye-cran40/' && \
    apt-get update && \
    apt-get install -y \
    r-base=4.4* \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the Rscript path explicitly
ENV PATH="/usr/lib/R/bin:${PATH}"

# Verify Rscript installation
RUN Rscript --version

# Install Bioconductor and CRAN packages
RUN R -e "install.packages('BiocManager', repos='https://cloud.r-project.org')" \
    && R -e "BiocManager::install(version = '3.20')" \
    && R -e "BiocManager::install('ggtree')" \
    && R -e "install.packages(c('ape', 'tidyverse'), repos='https://cloud.r-project.org')"

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Set the command to run your Streamlit app
CMD ["streamlit", "run", "Home.py"]
