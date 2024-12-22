FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=index.py

# Add health check endpoint
RUN echo 'from flask import Flask\n\
app = Flask(__name__)\n\
@app.route("/health")\n\
def health():\n\
    return "OK"' >> health.py

# Expose port
EXPOSE 5000

# Run with wait-for script
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "index:app"]