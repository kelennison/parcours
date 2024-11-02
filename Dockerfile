# Use a base image with Python and R 4.2
FROM rocker/r-ver:4.2.0

# Install general dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    unzip \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Bioconductor and other R packages
RUN R -e "install.packages('BiocManager', repos='https://cloud.r-project.org')" \
    && R -e "BiocManager::install('ggtree')" \
    && R -e "install.packages(c('ape', 'tidyverse'), repos='https://cloud.r-project.org')"

# Install Python 3.10 and Python dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python packages if needed
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Set the command to run your Streamlit app
CMD ["streamlit", "run", "Home.py"]
