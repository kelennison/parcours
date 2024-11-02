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

# Install littler and verify install2.r availability
RUN R -e "install.packages('littler', repos='https://cloud.r-project.org')"
RUN ln -s /usr/local/lib/R/site-library/littler/bin/r /usr/local/bin/install2.r \
    && ln -s /usr/local/lib/R/site-library/littler/bin/r /usr/local/bin/installBioc.r \
    && install2.r --help || (echo 'install2.r not found'; exit 1)

# Install Bioconductor and required packages with install2.r
RUN install2.r --error --deps TRUE \
    BiocManager \
    tidyverse \
    ape \
    ggtree

# Copy and install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]
