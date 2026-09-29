FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN playwright install --with-deps

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
