# Use the tidyverse Rocker image which already contains tidyverse and devtools
FROM rocker/tidyverse:4.4.1

# Set non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for Python, R graphics, and ggtree compilation
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

# Install R packages. 
# Using install_github as a fallback ensures we get the latest compatible version.
RUN R -e "install.packages('BiocManager', repos='https://cloud.r-project.org')" \
    && R -e "BiocManager::install('ggtree', update = FALSE, ask = FALSE)" \
    && R -e "install.packages('ape', repos='https://cloud.r-project.org')"

# Install Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "Home.py"]