# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Install R (adjust as necessary for your environment)
RUN apt-get update && apt-get install -y r-base

# Install R dependencies (if needed)
COPY install.R .
RUN Rscript install.R

# Expose the port that Streamlit runs on
EXPOSE 8501

# Command to run the Streamlit application
CMD ["streamlit", "run", "Home.py"]
