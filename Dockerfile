FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p images
RUN mkdir -p templates

EXPOSE 5000

CMD ["python", "index.py"]