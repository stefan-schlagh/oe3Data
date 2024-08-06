# Use an official Python runtime as the base image
FROM python:3.10.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for pandas
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev
    # \
    #&& rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY data /app

# Install pandas and requests
RUN pip install --no-cache-dir pandas requests

# Command to run when the container starts
CMD ["python", "./oe3crawler.py", "all"]