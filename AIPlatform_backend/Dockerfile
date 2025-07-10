FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PyQt5 runtime (not building from source)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create log directory structure
RUN mkdir -p /app/logs/backend && \
    chmod -R 777 /app/logs


# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --only-binary :all: --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

CMD ["python3", "main.py"]
