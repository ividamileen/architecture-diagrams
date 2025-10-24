FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    graphviz \
    default-jre \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download PlantUML
RUN wget -O /usr/local/bin/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2023.13/plantuml-1.2023.13.jar

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create diagram storage directory
RUN mkdir -p /app/diagrams

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
