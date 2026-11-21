FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .

# data.json will live in a volume so it persists across restarts
VOLUME /app/data

# Override DATA_FILE path via env so it writes to the volume
ENV DATA_FILE=/app/data/data.json

CMD ["python", "bot.py"]
