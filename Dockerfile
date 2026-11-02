# Start with a Rocker R base image
FROM rocker/r-ver:4.4.1

# Set non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Python and R package compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-tk \
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
    libtiff-dev \
    libjpeg-dev \
    git \
    libicu-dev \
    libpng-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Posit Package Manager (PPM)
# R 4.4.1 is based on Ubuntu Jammy (22.04)
ENV RSPM_CRAN=https://packagemanager.posit.co/cran/__linux__/jammy/latest
ENV RSPM_BIOC=https://packagemanager.posit.co/bioconductor/latest
ENV BIOCONDUCTOR_CONFIG_FILE=https://packagemanager.posit.co/bioconductor/latest/config.yaml

# Install R packages using PPM precompiled binaries
RUN R -e "install.packages('BiocManager', repos = c(CRAN = Sys.getenv('RSPM_CRAN')))" \
    && R -e "options(repos = c(CRAN = Sys.getenv('RSPM_CRAN')), BioC_mirror = Sys.getenv('RSPM_BIOC')); BiocManager::install('ggtree', update = FALSE, ask = FALSE)" \
    && R -e "install.packages('tidyverse', repos = c(CRAN = Sys.getenv('RSPM_CRAN')))" \
    && R -e "install.packages('ape', repos = c(CRAN = Sys.getenv('RSPM_CRAN')))"

# Install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]