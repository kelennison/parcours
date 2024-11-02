# Start with a Python base image
FROM python:3.10-slim

# Set R version and non-interactive frontend
ENV R_VERSION=4.4.1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for R and other required tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libreadline-dev \
    libbz2-dev \
    liblzma-dev \
    curl \
    libxml2-dev \
    libcairo2-dev \
    libsqlite3-dev \
    libmariadb-dev \
    libpq-dev \
    libssh2-1-dev \
    unixodbc-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libsodium-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install R
RUN wget -q https://cran.r-project.org/src/base/R-4/R-${R_VERSION}.tar.gz \
    && tar -xf R-${R_VERSION}.tar.gz \
    && cd R-${R_VERSION} \
    && ./configure --with-x=no \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf R-${R_VERSION} R-${R_VERSION}.tar.gz

# Set the Rscript path explicitly
ENV PATH="/usr/local/bin/R:${PATH}"

# Verify R installation
RUN Rscript --version

# Install Bioconductor and necessary CRAN packages with forced installations
RUN R -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager', repos='https://cloud.r-project.org'); \
    BiocManager::install(version = '3.20'); \
    BiocManager::install('ggtree', force = TRUE); \
    install.packages('tidyverse', repos='https://cloud.r-project.org', dependencies=TRUE); \
    install.packages('ape', repos='https://cloud.r-project.org', dependencies=TRUE)"

# Copy and install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]
