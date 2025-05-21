FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYQT5_LICENSE_CONFIRMED=1

WORKDIR /workspace

# Install dependencies and bash
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    curl \
    git \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    ca-certificates \
    wget \
    sudo \
    gnupg && \
    rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install MongoDB tools
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor > /usr/share/keyrings/mongodb-server.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/mongodb-server.gpg] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

COPY . .


# CMD ["uv", "python", "--help"]
CMD ["sleep", "infinity"]
