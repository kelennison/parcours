# Start with the official Python base image
FROM python:3.10

# Environment variables to prevent interaction during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    dirmngr \
    gnupg \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libcairo2-dev \
    libtiff-dev \
    libjpeg-dev \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add the R repository to get the latest R version
RUN wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/cran.gpg && \
    add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/" && \
    apt-get update && \
    apt-get install -y --no-install-recommends r-base r-base-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install R packages from CRAN and Bioconductor
RUN R -e "install.packages(c('BiocManager', 'tidyverse', 'ape'))" && \
    R -e "BiocManager::install(c('ggtree', 'ragg'), version = '3.20')"

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code
COPY . /app
WORKDIR /app

# Set Streamlit to run the app
CMD ["streamlit", "run", "Home.py"]
