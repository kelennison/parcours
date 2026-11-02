# Start with a Rocker R base image
FROM rocker/r-ver:4.4.1

# Set non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Python AND R package compilation
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

# Set Posit Package Manager (PPM) to use precompiled binaries for FAST installation
ENV RSPM=https://packagemanager.posit.co/cran/__linux__/jammy/latest

# Install R packages using PPM for speed and reliability
RUN R -e "options(repos = c(CRAN = Sys.getenv('RSPM'))); install.packages('BiocManager')" \
    && R -e "options(repos = c(CRAN = Sys.getenv('RSPM'))); BiocManager::install('ggtree', update = FALSE, ask = FALSE)" \
    && R -e "options(repos = c(CRAN = Sys.getenv('RSPM'))); install.packages('tidyverse')" \
    && R -e "options(repos = c(CRAN = Sys.getenv('RSPM'))); install.packages('ape')"

# Install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]