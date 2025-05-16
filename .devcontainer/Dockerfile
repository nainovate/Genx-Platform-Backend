FROM debian:bookworm

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

# Install mongodb tools
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor > /usr/share/keyrings/mongodb-server.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/mongodb-server.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# # Create user
# ARG USERNAME=vscode
# ARG USER_UID=1000
# ARG USER_GID=1000

# RUN groupadd --gid $USER_GID $USERNAME && \
#     useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
#     echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
#     chmod 0440 /etc/sudoers.d/$USERNAME

# USER $USERNAME

COPY . .

# Temporary fix for .venv ignore in .dockerignore
# RUN rm -rf .venv

# CMD ["uv", "python", "--help"]
CMD ["sleep", "infinity"]