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

# Copy your project files
COPY . .

# Install R packages
RUN Rscript install.R

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Set the command to run your Streamlit app
CMD ["streamlit", "run", "Home.py"]
