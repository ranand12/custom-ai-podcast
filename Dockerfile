# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with specific order
RUN pip install --no-cache-dir lxml>=4.9.3 && \
    pip install --no-cache-dir lxml_html_clean && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for temp files and output
RUN mkdir -p temp output

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Command to run the application
CMD streamlit run --server.port $PORT --server.address $HOST app_ui.py 